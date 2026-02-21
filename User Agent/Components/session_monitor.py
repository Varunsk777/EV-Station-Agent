from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import threading
import math

from config.ua_config import UAConfig
from utils.logger import get_logger


# DATA MODELS
@dataclass
class LatLon:
    lat: float
    lon: float


@dataclass
class Reservation:
    reservation_id: str
    station_id: str
    slot_id: str
    vehicle_id: str
    start_time: str  # ISO 8601
    duration_min: int
    status: str


@dataclass
class TelemetryData:
    charging_progress_pct: float
    power_kw: float
    energy_kwh: float
    session_status: str
    timestamp: str


@dataclass
class FaultAlert:
    fault_type: str
    severity: str  # LOW / MEDIUM / CRITICAL
    station_id: str
    slot_id: str
    timestamp: str


@dataclass
class DelayResult:
    reservation_id: str
    new_eta: str
    delay_minutes: int
    severity: str  # MINOR / MAJOR / NO_SHOW


@dataclass
class SessionResult:
    session_id: str
    reservation_id: str
    station_id: str
    actual_cost: float
    actual_wait_min: int
    distance_km: float
    energy_delivered_kwh: float
    session_start: str
    session_end: str
    user_satisfaction: Optional[int]
    chosen_station_rank: int


# SESSION MONITOR

class SessionMonitor:

    def __init__(self, vehicle_id: str):

        self.logger = get_logger("SessionMonitor")
        self.config = UAConfig()
        self.vehicle_id = vehicle_id

        self._lock = threading.Lock()

        self._reservation: Optional[Reservation] = None
        self._station_location: Optional[LatLon] = None
        self._last_gps: Optional[LatLon] = None
        self._telemetry: Optional[TelemetryData] = None
        self._session_start_time: Optional[datetime] = None
        self._last_telemetry_time: Optional[datetime] = None

        self.logger.info("SessionMonitor initialized.")

    # SESSION INIT

    def start_session_monitoring(
        self,
        reservation: Reservation,
        station_location: LatLon,
    ):
       
        with self._lock:
            self._reservation = reservation
            self._station_location = station_location
            self._session_start_time = None
            self._telemetry = None
            self._last_telemetry_time = None

        self.logger.info(
            f"Monitoring reservation {reservation.reservation_id}"
        )

    # ETA TRACKING

    def update_eta(self, current_gps: LatLon) -> Optional[DelayResult]:
        
        with self._lock:

            if not self._reservation or not self._station_location:
                return None

            self._last_gps = current_gps

            eta_minutes = self._estimate_eta_minutes(
                current_gps,
                self._station_location
            )

            new_eta_time = datetime.utcnow() + timedelta(minutes=eta_minutes)

            reserved_start = datetime.fromisoformat(
                self._reservation.start_time
            )

            delay_minutes = int(
                (new_eta_time - reserved_start).total_seconds() / 60
            )

            if delay_minutes <= 0:
                return None

            if delay_minutes >= self.config.no_show_threshold_min:
                severity = "NO_SHOW"
            elif delay_minutes >= self.config.major_delay_threshold_min:
                severity = "MAJOR"
            else:
                severity = "MINOR"

            self.logger.warning(
                f"Delay detected: {delay_minutes} min ({severity})"
            )

            return DelayResult(
                reservation_id=self._reservation.reservation_id,
                new_eta=new_eta_time.isoformat(),
                delay_minutes=delay_minutes,
                severity=severity,
            )

    # TELEMETRY HANDLING

    def receive_telemetry(self, data: TelemetryData):

        with self._lock:
            self._telemetry = data
            self._last_telemetry_time = datetime.utcnow()

            if data.session_status == "IN_PROGRESS" and not self._session_start_time:
                self._session_start_time = datetime.utcnow()

    def telemetry_timeout_detected(self) -> bool:
        
        if not self._last_telemetry_time:
            return False

        delta = datetime.utcnow() - self._last_telemetry_time

        if delta.total_seconds() > self.config.telemetry_timeout_sec:
            self.logger.warning("Telemetry timeout detected.")
            return True

        return False

    # FAULT HANDLING

    def handle_fault(self, alert: FaultAlert) -> bool:
        
        self.logger.error(
            f"Fault: {alert.fault_type} (Severity: {alert.severity})"
        )

        if alert.severity == "CRITICAL":
            self.logger.error("Critical fault — cancellation required.")
            return True

        return False

    # SESSION STATUS CHECK

    def check_session_status(self) -> bool:
        """
        Returns True if session completed.
        """

        if not self._telemetry:
            return False

        return self._telemetry.session_status == "COMPLETED"

    # SESSION COMPLETION

    def detect_session_complete(self) -> Optional[SessionResult]:

        if not self._reservation or not self._telemetry:
            return None

        end_time = datetime.utcnow()

        wait_minutes = 0
        if self._session_start_time:
            wait_minutes = int(
                (self._session_start_time -
                 datetime.fromisoformat(self._reservation.start_time)
                 ).total_seconds() / 60
            )

        distance_km = 0
        if self._last_gps and self._station_location:
            distance_km = self._haversine(
                self._last_gps,
                self._station_location
            )

        return SessionResult(
            session_id=f"session_{self._reservation.reservation_id}",
            reservation_id=self._reservation.reservation_id,
            station_id=self._reservation.station_id,
            actual_cost=0.0,  # Integrate billing later
            actual_wait_min=max(wait_minutes, 0),
            distance_km=distance_km,
            energy_delivered_kwh=self._telemetry.energy_kwh,
            session_start=self._session_start_time.isoformat()
            if self._session_start_time else None,
            session_end=end_time.isoformat(),
            user_satisfaction=None,
            chosen_station_rank=1,
        )

    # HELPER FUNCTIONS


    def _estimate_eta_minutes(self, current: LatLon, target: LatLon) -> int:
       
        distance_km = self._haversine(current, target)

        avg_speed_kmph = self.config.default_avg_speed_kmph
        eta_hours = distance_km / avg_speed_kmph

        return int(eta_hours * 60)

    def _haversine(self, loc1: LatLon, loc2: LatLon) -> float:
        R = 6371.0

        lat1 = math.radians(loc1.lat)
        lon1 = math.radians(loc1.lon)
        lat2 = math.radians(loc2.lat)
        lon2 = math.radians(loc2.lon)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1)
            * math.cos(lat2)
            * math.sin(dlon / 2) ** 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c
