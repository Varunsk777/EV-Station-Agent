from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum


# UA -> CA : CHARGING REQUEST
@dataclass
class ChargingRequest:
    user_id: str
    vehicle_id: str
    urgency_level: str
    vehicle_context: Dict
    preference_weights: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def validate(self):
        if not self.user_id:
            raise ValueError("user_id required")

        if not self.vehicle_id:
            raise ValueError("vehicle_id required")

        if not self.preference_weights:
            raise ValueError("preference_weights required")

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "vehicle_id": self.vehicle_id,
            "urgency_level": self.urgency_level,
            "vehicle_context": self.vehicle_context,
            "preference_weights": self.preference_weights,
            "timestamp": self.timestamp.isoformat(),
        }


# CA -> UA : RANKED STATION RESPONSE
@dataclass
class RankedStationsResponse:
    request_id: str
    stations: List[Dict]
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def validate(self):
        if not self.stations:
            raise ValueError("Station list cannot be empty")


# UA -> CA : STATION SELECTION
@dataclass
class StationSelection:
    request_id: str
    station_id: str
    user_id: str
    vehicle_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def validate(self):
        if not self.station_id:
            raise ValueError("station_id required")

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "station_id": self.station_id,
            "user_id": self.user_id,
            "vehicle_id": self.vehicle_id,
            "timestamp": self.timestamp.isoformat(),
        }


# CA -> UA : RESERVATION CONFIRMATION
@dataclass
class ReservationConfirmation:
    reservation_id: str
    station_id: str
    slot_id: str
    slot_start_time_iso: str
    slot_end_time_iso: str
    reserved_price: float

    def validate(self):
        if self.reserved_price < 0:
            raise ValueError("reserved_price cannot be negative")


# UA -> CA : DELAY REPORT
@dataclass
class DelayReport:
    reservation_id: str
    updated_arrival_iso: str
    delay_minutes: float
    severity: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def validate(self):
        if self.delay_minutes < 0:
            raise ValueError("delay_minutes cannot be negative")

    def to_dict(self) -> dict:
        return {
            "reservation_id": self.reservation_id,
            "updated_arrival_iso": self.updated_arrival_iso,
            "delay_minutes": self.delay_minutes,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
        }
# UA -> CA : CANCELLATION REQUEST
@dataclass
class CancellationRequest:
    reservation_id: str
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "reservation_id": self.reservation_id,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }


# SA -> UA : TELEMETRY UPDATE
@dataclass
class TelemetryUpdateMessage:
    reservation_id: str
    battery_soc: float
    charging_power_kw: float
    energy_delivered_kwh: float
    timestamp: datetime

    def validate(self):
        if not (0 <= self.battery_soc <= 100):
            raise ValueError("battery_soc must be 0–100")

        if self.charging_power_kw < 0:
            raise ValueError("charging_power_kw cannot be negative")

        if self.energy_delivered_kwh < 0:
            raise ValueError("energy_delivered_kwh cannot be negative")
# SA -> UA : MICRO SLOT OFFER
@dataclass
class MicroSlotOfferMessage:
    reservation_id: str
    slot_id: str
    start_time_iso: str
    end_time_iso: str
    price_modifier: float
    expires_at_iso: str

    def validate(self):
        if self.price_modifier <= 0:
            raise ValueError("price_modifier must be positive")

# SA -> UA : FAULT ALERT
class FaultSeverity(str, Enum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class FaultAlertMessage:
    reservation_id: str
    station_id: str
    fault_code: str
    description: str
    severity: FaultSeverity
    timestamp: datetime = field(default_factory=datetime.utcnow)