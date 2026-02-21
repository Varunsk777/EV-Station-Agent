from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple


# URGENCY LEVEL ENUM
class UrgencyLevel(str, Enum):
    EMERGENCY = "EMERGENCY"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

# GPS LOCATION MODEL
@dataclass
class GPSLocation:
    latitude: float
    longitude: float

    def as_tuple(self) -> Tuple[float, float]:
        return (self.latitude, self.longitude)


# VEHICLE CONTEXT MODEL
@dataclass
class VehicleContext:
    vehicle_id: str

    # Battery & Energy
    state_of_charge: float  # Percentage (0–100)
    estimated_range_km: float

    # Location
    current_location: GPSLocation
    destination: Optional[GPSLocation] = None
    distance_to_destination_km: Optional[float] = None

    # Charging
    charging_power_limit_kw: Optional[float] = None
    battery_capacity_kwh: Optional[float] = None

    # Derived
    urgency_level: UrgencyLevel = field(default=UrgencyLevel.LOW)

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # VALIDATION
    def __post_init__(self):
        if not (0 <= self.state_of_charge <= 100):
            raise ValueError("state_of_charge must be between 0 and 100")

        if self.estimated_range_km < 0:
            raise ValueError("estimated_range_km cannot be negative")

        if self.distance_to_destination_km is not None:
            if self.distance_to_destination_km < 0:
                raise ValueError("distance_to_destination_km cannot be negative")

    # URGENCY COMPUTATION
    def compute_urgency(
        self,
        emergency_threshold: float = 10.0,
        high_threshold: float = 25.0,
        medium_threshold: float = 50.0,
    ) -> UrgencyLevel:

        soc = self.state_of_charge

        if soc <= emergency_threshold:
            self.urgency_level = UrgencyLevel.EMERGENCY

        elif soc <= high_threshold:
            self.urgency_level = UrgencyLevel.HIGH

        elif soc <= medium_threshold:
            self.urgency_level = UrgencyLevel.MEDIUM

        else:
            self.urgency_level = UrgencyLevel.LOW

        return self.urgency_level

    # RANGE SAFETY CHECK
    def can_reach_destination(self) -> bool:

        if (
            self.destination is None
            or self.distance_to_destination_km is None
        ):
            return True  # No destination constraint

        return self.estimated_range_km >= self.distance_to_destination_km

    # SERIALIZATION

    def to_dict(self) -> dict:
        return {
            "vehicle_id": self.vehicle_id,
            "state_of_charge": self.state_of_charge,
            "estimated_range_km": self.estimated_range_km,
            "current_location": {
                "latitude": self.current_location.latitude,
                "longitude": self.current_location.longitude,
            },
            "destination": {
                "latitude": self.destination.latitude,
                "longitude": self.destination.longitude,
            }
            if self.destination
            else None,
            "distance_to_destination_km": self.distance_to_destination_km,
            "charging_power_limit_kw": self.charging_power_limit_kw,
            "battery_capacity_kwh": self.battery_capacity_kwh,
            "urgency_level": self.urgency_level.value,
            "timestamp": self.timestamp.isoformat(),
        }

    # STRING REPRESENTATION
    def __str__(self):
        return (
            f"VehicleContext(vehicle_id={self.vehicle_id}, "
            f"SoC={self.state_of_charge}%, "
            f"Range={self.estimated_range_km}km, "
            f"Urgency={self.urgency_level})"
        )