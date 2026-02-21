from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import json
import os
# DATA MODEL
@dataclass
class PreferenceWeights:
    w_cost: float = 0.33
    w_wait: float = 0.33
    w_distance: float = 0.34

    def normalize(self):
        total = self.w_cost + self.w_wait + self.w_distance
        if total == 0:
            self.w_cost = self.w_wait = self.w_distance = 1 / 3
            return

        self.w_cost /= total
        self.w_wait /= total
        self.w_distance /= total

    def enforce_floor(self, min_weight: float):
        self.w_cost = max(self.w_cost, min_weight)
        self.w_wait = max(self.w_wait, min_weight)
        self.w_distance = max(self.w_distance, min_weight)
        self.normalize()
# PREFERENCE MANAGER
class PreferenceManager:
    def __init__(
        self,
        user_id: str,
        storage_path: str = "preference_store.json",
        learning_rate: float = 0.05,
        min_weight_floor: float = 0.05,
    ):

        self.user_id = user_id
        self.storage_path = storage_path
        self.learning_rate = learning_rate
        self.min_weight_floor = min_weight_floor

        self.weights = PreferenceWeights()
        self.session_history: List[dict] = []

        self._load_preferences()
    # LOAD & SAVE
    def _load_preferences(self):
        if not os.path.exists(self.storage_path):
            return

        with open(self.storage_path, "r") as f:
            data = json.load(f)

        user_data = data.get(self.user_id)
        if not user_data:
            return

        self.weights = PreferenceWeights(**user_data["weights"])
        self.session_history = user_data.get("history", [])

    def persist_weights(self):
        data = {}
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r") as f:
                data = json.load(f)

        data[self.user_id] = {
            "weights": asdict(self.weights),
            "history": self.session_history,
        }

        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=4)
    
    # GETTERS
    def get_preference_params(self) -> Dict[str, float]:
        """
        Used by UA to send weights to CA.
        """
        return asdict(self.weights)

    # EXPLICIT UPDATE
    def update_explicit_preference(self, key: str, value: float):
        if key not in ["w_cost", "w_wait", "w_distance"]:
            raise ValueError("Invalid preference key")

        setattr(self.weights, key, value)
        self.weights.normalize()
        self.weights.enforce_floor(self.min_weight_floor)

    def reset_to_defaults(self):
        self.weights = PreferenceWeights()
        self.weights.normalize()
        self.session_history = []

    # SESSION RECORDING
    def record_session(self, session_result):
        """
        Store session outcome for learning.
        session_result expected to contain:
            - station_id
            - cost_score
            - wait_score
            - distance_score
            - satisfaction (0–1)
        """
        self.session_history.append(session_result)

        # Optional: limit history size
        if len(self.session_history) > 100:
            self.session_history.pop(0)

    # LEARNING LOGIC
    def update_weights(self, session: dict, chosen: Optional[str] = None):
        satisfaction = session.get("satisfaction", 0.5)

        cost_score = session.get("cost_score", 0.5)
        wait_score = session.get("wait_score", 0.5)
        distance_score = session.get("distance_score", 0.5)

        # Weight updates proportional to satisfaction and feature score
        self.weights.w_cost += self.learning_rate * satisfaction * cost_score
        self.weights.w_wait += self.learning_rate * satisfaction * wait_score
        self.weights.w_distance += (
            self.learning_rate * satisfaction * distance_score
        )

        # Normalize & enforce floor
        self.weights.normalize()
        self.weights.enforce_floor(self.min_weight_floor)

    # DEBUG
    def __str__(self):
        return (
            f"PreferenceWeights("
            f"cost={self.weights.w_cost:.3f}, "
            f"wait={self.weights.w_wait:.3f}, "
            f"distance={self.weights.w_distance:.3f})"
        )