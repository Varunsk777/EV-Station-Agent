from dataclasses import dataclass, field
from typing import List, Optional
import threading

from config.ua_config import UAConfig
from utils.logger import get_logger


# DATA MODELS
@dataclass
class PreferenceSettings:
    max_cost_per_session: float
    max_wait_minutes: int
    max_distance_km: float


@dataclass
class WeightVector:
    w_cost: float
    w_wait: float
    w_distance: float


@dataclass
class PreferenceParams:
    w_cost: float
    w_wait: float
    w_distance: float
    max_cost_per_session: float
    max_wait_minutes: int
    max_distance_km: float


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


# PREFERENCE MANAGER
class PreferenceManager:
    def __init__(self, user_id: str):

        self.logger = get_logger("PreferenceManager")
        self.config = UAConfig()
        self.user_id = user_id

        self._lock = threading.Lock()

        self.weights = WeightVector(
            w_cost=0.33,
            w_wait=0.33,
            w_distance=0.34,
        )

        self.explicit_prefs = PreferenceSettings(
            max_cost_per_session=1000.0,
            max_wait_minutes=30,
            max_distance_km=20.0,
        )

        self.session_history: List[SessionResult] = []

        self.logger.info("PreferenceManager initialized.")

    # LOAD / GET
    def load_preferences(self):
        """
        Placeholder for server load.
        """
        self.logger.info("Loading preferences from server (stub).")

    def get_preference_params(self) -> PreferenceParams:
        """
        Returns structured preference parameters for CA request.
        """

        with self._lock:
            return PreferenceParams(
                w_cost=self.weights.w_cost,
                w_wait=self.weights.w_wait,
                w_distance=self.weights.w_distance,
                max_cost_per_session=self.explicit_prefs.max_cost_per_session,
                max_wait_minutes=self.explicit_prefs.max_wait_minutes,
                max_distance_km=self.explicit_prefs.max_distance_km,
