from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional
import threading

from config.ua_config import UAConfig
from utils.logger import get_logger


# ENUMS

class UrgencyLevel(Enum):
    EMERGENCY = "EMERGENCY"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# RAW DATA STRUCTURES

@dataclass
class LatLon:
    lat: float
    lon: float


@dataclass
class Waypoint:
    lat: float
    lon: float


@dataclass
class RawVehicleData:
    gps_location: LatLon
    state_of_charge: float
    remaining_range_km: float
    destination: Optional[LatLon]
    planned_route: List[Waypoint]
    current_datetime: datetime
    user_trigger: bool


# STRUCTURED CONTEXT MODEL

@dataclass
class VehicleContext:
    vehicle_id: str
    timestamp: datetime
    gps_location: LatLon
    state_of_charge: float
    remaining_range_km: float
    destination: Optional[LatLon]
    planned_route: List[Waypoint]
    urgency_level: UrgencyLevel


# CONTEXT MANAGER

class ContextManager:
def __init__(self, vehicle_id: str):

        self.logger = get_logger("ContextManager")
        self.vehicle_id = vehicle_id
        self.config = UAConfig()

        self._lock = threading.Lock()
        self._last_snapshot: Optional[VehicleContext] = None

        self.logger.info("ContextManager initialized.")

    # SENSOR COLLECTION (SIMULATION STUB)
    def collect_vehicle_data(self) -> RawVehicleData:
        gps = LatLon(lat=12.9716, lon=77.5946)
        soc = 0.32  
        remaining_range = 120.0
        destination = LatLon(lat=12.9352, lon=77.6245)
        route = []
        now = datetime.utcnow()
        user_trigger = False

        return RawVehicleData(
            gps_location=gps,
            state_of_charge=soc,
            remaining_range_km=remaining_range,
            destination=destination,
            planned_route=route,
            current_datetime=now,
            user_trigger=user_trigger,
        )

    # URGENCY CLASSIFICATION
    def compute_urgency(self, soc: float) -> UrgencyLevel:
        if soc <= self.config.soc_emergency_threshold:
            return UrgencyLevel.EMERGENCY

        elif soc <= self.config.soc_high_threshold:
            return UrgencyLevel.HIGH

        elif soc <= self.config.soc_medium_threshold:
            return UrgencyLevel.MEDIUM

        else:
            return UrgencyLevel.LOW

    # CONTEXT BUILDING
    def build_vehicle_context(self, raw: RawVehicleData) -> VehicleContext:
        urgency = self.compute_urgency(raw.state_of_charge)

        return VehicleContext(
            vehicle_id=self.vehicle_id,
            timestamp=raw.current_datetime,
            gps_location=raw.gps_location,
            state_of_charge=raw.state_of_charge,
            remaining_range_km=raw.remaining_range_km,
            destination=raw.destination,
            planned_route=raw.planned_route,
            urgency_level=urgency,
        )

    # CHARGING TRIGGER LOGIC
    def should_trigger_charging(self, ctx: VehicleContext) -> bool:
        # Condition 1: SoC below configured trigger threshold
        if ctx.state_of_charge <= self.config.soc_trigger_threshold:
            self.logger.info("Trigger: SoC below threshold.")
            return True

        # Condition 2: Remaining range insufficient to reach destination
        if ctx.destination:
            distance_to_dest = self._estimate_distance(
                ctx.gps_location,
                ctx.destination
            )

            if ctx.remaining_range_km < distance_to_dest:
                self.logger.warning(
                    "Trigger: Remaining range insufficient for destination."
                )
                return True

        # Condition 3: User manual trigger
        # (requires raw data; simplified assumption)
        raw_data = self.collect_vehicle_data()
        if raw_data.user_trigger:
            self.logger.info("Trigger: Manual user request.")
            return True

        # Condition 4: Scheduled pre-departure (optional extension)
        if self.config.enable_scheduled_trigger:
            if self._scheduled_departure_trigger():
                self.logger.info("Trigger: Scheduled departure.")
                return True

        return False

    # PUBLIC SNAPSHOT METHOD
    def get_current_snapshot(self) -> VehicleContext:
       
        with self._lock:
            raw = self.collect_vehicle_data()
            snapshot = self.build_vehicle_context(raw)
            self._last_snapshot = snapshot
            return snapshot

    # HELPER FUNCTIONS
    def _estimate_distance(self, loc1: LatLon, loc2: LatLon) -> float:
    
        from math import radians, sin, cos, sqrt, atan2

        R = 6371.0  # Earth radius in km

        dlat = radians(loc2.lat - loc1.lat)
        dlon = radians(loc2.lon - loc1.lon)

        a = (
            sin(dlat / 2) ** 2
            + cos(radians(loc1.lat))
            * cos(radians(loc2.lat))
            * sin(dlon / 2) ** 2
        )

        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def _scheduled_departure_trigger(self) -> bool:
        """
        Placeholder for calendar-based trigger logic.
        """
        return False
