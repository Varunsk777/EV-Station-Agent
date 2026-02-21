from dataclasses import dataclass
from typing import List, Optional
import threading
from utils.logger import get_logger

# DATA MODELS
@dataclass(frozen=True)
class StationOption:
    station_id: str
    station_name: str
    rank: int
    estimated_wait_min: int
    estimated_cost: float
    distance_km: float
    available_slots: int
    charger_type: str
    power_kw: float
    operator: str


@dataclass
class MicroSlotOffer:
    micro_slot_id: str
    station_id: str
    available_window_start: str
    available_window_end: str


@dataclass
class SelectionResult:
    action: str
    station_id: Optional[str]

# RECOMMENDATION MANAGER
class RecommendationManager:

    def __init__(self):

        self.logger = get_logger("RecommendationManager")
        self._lock = threading.Lock()

        self._ranked_stations: List[StationOption] = []
        self._deferred = False
        self._pending_micro_offer: Optional[MicroSlotOffer] = None

        self.logger.info("RecommendationManager initialized.")

    # RECEIVE RANKED LIST (IMMUTABLE)
    def receive_ranked_stations(self, stations: List[StationOption]):
        with self._lock:
            self._ranked_stations = list(stations)
            self._deferred = False

        self.logger.info(f"Received {len(stations)} ranked stations from CA.")

    # DISPLAY
    def display_stations(self) -> List[StationOption]:
        with self._lock:
            return list(self._ranked_stations)

    # USER ACTION HANDLING

    def handle_user_selection(
        self,
        action: str,
        station_id: Optional[str] = None,
    ) -> SelectionResult:

        action = action.upper()

        with self._lock:

            if action == "ACCEPT":
                if not station_id:
                    raise ValueError("Station ID required for ACCEPT")

                if not any(s.station_id == station_id for s in self._ranked_stations):
                    raise ValueError("Invalid station ID — not in CA list")

                self.logger.info(f"User accepted station: {station_id}")
                return SelectionResult(action="ACCEPT", station_id=station_id)

            elif action == "REJECT":
                self.logger.info("User rejected current option.")
                return SelectionResult(action="REJECT", station_id=None)

            elif action == "DEFER":
                self._deferred = True
                self.logger.info("User deferred station selection.")
                return SelectionResult(action="DEFER", station_id=None)

            else:
                raise ValueError("Invalid action. Use ACCEPT/REJECT/DEFER")

    # DEFER

    def handle_defer(self):
        """
        Preserve ranked list and wait for resume.
        """

        with self._lock:
            self._deferred = Tr_
