import time
import threading
from enum import Enum
from typing import Optional

# Component imports (assumed available in project structure)
from components.context_manager import ContextManager
from components.preference_manager import PreferenceManager
from components.recommendation_manager import RecommendationManager
from components.session_monitor import SessionMonitor

from communication.ca_client import CAClient
from communication.sa_client import SAClient

from storage.local_cache import LocalCache
from config.ua_config import UAConfig
from utils.logger import get_logger


class UAState(Enum):
    IDLE = "IDLE"
    MONITORING = "MONITORING"
    REQUESTING_STATIONS = "REQUESTING_STATIONS"
    AWAITING_USER_SELECTION = "AWAITING_USER_SELECTION"
    RESERVATION_CONFIRMED = "RESERVATION_CONFIRMED"
    SESSION_ACTIVE = "SESSION_ACTIVE"
    SESSION_COMPLETED = "SESSION_COMPLETED"
    DEFERRED = "DEFERRED"
    ERROR = "ERROR"


class UAOrchestrator:
       def __init__(self, user_id: str, vehicle_id: str):

        self.logger = get_logger("UAOrchestrator")

        # Core identifiers
        self.user_id = user_id
        self.vehicle_id = vehicle_id

        # Configuration
        self.config = UAConfig()

        # Components
        self.context_manager = ContextManager(vehicle_id)
        self.preference_manager = PreferenceManager(user_id)
        self.recommendation_manager = RecommendationManager()
        self.session_monitor = SessionMonitor(vehicle_id)

        # Communication clients
        self.ca_client = CAClient()
        self.sa_client = SAClient()

        # Local short-term memory
        self.cache = LocalCache()

        # State
        self.state = UAState.IDLE
        self.running = False

        # Lock for thread safety
        self._lock = threading.Lock()

        self.logger.info("UA Orchestrator initialized.")

    # MAIN CONTROL LOOP

    def start(self):
        """
        Starts UA monitoring loop.
        """
        self.logger.info("Starting UA Orchestrator loop.")
        self.running = True
        self.state = UAState.MONITORING

        while self.running:
            try:
                self._run_cycle()
                time.sleep(self.config.poll_interval_sec)

            except Exception as e:
                self.logger.exception(f"Critical error in orchestrator: {e}")
                self.state = UAState.ERROR
                time.sleep(self.config.error_retry_delay_sec)

    def stop(self):
        """
        Stops UA loop.
        """
        self.logger.info("Stopping UA Orchestrator.")
        self.running = False

    # SINGLE LOOP CYCLE

    def _run_cycle(self):
        """
        Executes one orchestration cycle.
        """

        if self.state == UAState.MONITORING:
            self._handle_monitoring()

        elif self.state == UAState.REQUESTING_STATIONS:
            self._request_stations_from_ca()

        elif self.state == UAState.AWAITING_USER_SELECTION:
            # Waiting state — handled via callback/event
            pass

        elif self.state == UAState.RESERVATION_CONFIRMED:
            self._start_session_monitoring()

        elif self.state == UAState.SESSION_ACTIVE:
            self._monitor_session()

        elif self.state == UAState.SESSION_COMPLETED:
            self._finalize_session()

        elif self.state == UAState.DEFERRED:
            # Wait until user resumes
            pass

    # STEP 1–2: CONTEXT COLLECTION + TRIGGER

    def _handle_monitoring(self):
        """
        Collect vehicle context and evaluate charging trigger.
        """

        ctx = self.context_manager.get_current_snapshot()
        self.cache.current_vehicle_context = ctx

        if self.context_manager.should_trigger_charging(ctx):
            self.logger.info("Charging trigger activated.")
            self.state = UAState.REQUESTING_STATIONS

    # STEP 3–5: BUILD REQUEST & SEND TO CA

    def _request_stations_from_ca(self):
        """
        Build request and send to CA.
        """

        self.logger.info("Requesting ranked stations from CA.")

        vehicle_context = self.cache.current_vehicle_context
        preference_params = self.preference_manager.get_preference_params()

        try:
            ranked_stations = self.ca_client.send_charging_request(
                vehicle_context=vehicle_context,
                preference_params=preference_params,
                urgency_level=vehicle_context.urgency_level,
            )

            if not ranked_stations:
                self.logger.warning("No stations returned by CA.")
                self.state = UAState.MONITORING
                return

            self.cache.ranked_stations_cache = ranked_stations
            self.recommendation_manager.receive_ranked_stations(ranked_stations)

            self.state = UAState.AWAITING_USER_SELECTION

        except Exception as e:
            self.logger.error(f"CA unreachable: {e}")
            self.state = UAState.MONITORING

    # STEP 6–8: USER SELECTION FLOW

    def handle_user_action(self, action: str, station_id: Optional[str] = None):
        """
        External entry point called by UI/HMI.
        """

        with self._lock:

            result = self.recommendation_manager.handle_user_selection(
                action, station_id
            )

            if action == "ACCEPT" and station_id:
                self._confirm_reservation(station_id)

            elif action == "REJECT":
                self.logger.info("User rejected option.")
                # Remain in selection state

            elif action == "DEFER":
                self.logger.info("User deferred selection.")
                self.state = UAState.DEFERRED

    def _confirm_reservation(self, station_id: str):
        """
        Forward station selection to CA for reservation.
        """

        try:
            reservation = self.ca_client.confirm_station_selection(station_id)

            self.cache.active_reservation = reservation
            self.state = UAState.RESERVATION_CONFIRMED

            self.logger.info(
                f"Reservation confirmed: {reservation.reservation_id}"
            )

        except Exception as e:
            self.logger.error(f"Reservation failed: {e}")
            self.state = UAState.MONITORING

    # STEP 9: SESSION MONITORING
    def _start_session_monitoring(self):
        """
        Initialize session monitor.
        """

        reservation = self.cache.active_reservation
        self.session_monitor.start_session_monitoring(reservation)

        self.state = UAState.SESSION_ACTIVE
        self.logger.info("Session monitoring started.")

    def _monitor_session(self):
        """
        Track active charging session.
        """

        session_complete = self.session_monitor.check_session_status()

        if session_complete:
            self.cache.session_result = (
                self.session_monitor.detect_session_complete()
            )
            self.state = UAState.SESSION_COMPLETED

    # STEP 10–11: SESSION COMPLETION + PREF UPDATE
    def _finalize_session(self):
        """
        Finalize session and update preferences.
        """

        result = self.cache.session_result

        if result:
            self.preference_manager.record_session(result)
            self.preference_manager.update_weights(
                session=result,
                chosen=result.station_id,
            )
            self.preference_manager.persist_weights()

        self.logger.info("Session finalized and preferences updated.")

        self._reset_workflow()

    # RESET WORKFLOW
    def _reset_workflow(self):
        """
        Clears short-term state and returns to monitoring.
        """

        self.cache.clear_session_data()
        self.state = UAState.MONITORING

    # MICRO-SLOT HANDLING
    def handle_micro_slot_offer(self, offer):
        """
        Called when SA sends micro-slot offer.
        """

        self.cache.pending_micro_slot_offer = offer
        self.recommendation_manager.handle_micro_slot_offer(offer)

    def handle_micro_slot_decision(self, slot_id: str, decision: str):
        """
        Forward decision to SA.
        """

        self.sa_client.send_micro_slot_decision(slot_id, decision)
        self.logger.info(f"Micro-slot decision sent: {decision}")

    # DELAY REPORTING
    def process_delay_update(self, gps_data):
        """
        Called periodically with GPS updates.
        """

        delay_result = self.session_monitor.detect_delay(gps_data)

        if delay_result:
            self.session_monitor.send_delay_notification(delay_result)

            # Also inform CA
            self.ca_client.send_delay_report(delay_result)

    # ERROR HANDLING
    def handle_fault_alert(self, alert):
        """
        Handle charger fault from SA.
        """

        self.logger.warning(f"Fault alert received: {alert.fault_type}")

        cancellation_required = self.session_monitor.handle_fault(alert)

        if cancellation_required:
            self.ca_client.request_slot_cancellation(
                self.cache.active_reservation.reservation_id,
                reason="FAULT",
            )
            self.state = UAState.MONITORING
