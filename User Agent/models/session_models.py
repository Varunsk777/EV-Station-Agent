from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

# ENUMS
class SessionStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    EN_ROUTE = "EN_ROUTE"
    ARRIVED = "ARRIVED"
    CHARGING = "CHARGING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DelaySeverity(str, Enum):
    MINOR = "MINOR"
    MAJOR = "MAJOR"


class FaultSeverity(str, Enum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

# TELEMETRY MODEL
@dataclass
class TelemetryData:
    timestamp: datetime
    battery_soc: float
    charging_power_kw: float
    energy_delivered_kwh: float

    def __post_init__(self):
        if not (0 <= self.battery_soc <= 100):
            raise ValueError("battery_soc must be between 0 and 100")

        if self.charging_power_kw < 0:
            raise ValueError("charging_power_kw cannot be negative")

        if self.energy_delivered_kwh < 0:
            raise ValueError("energy_delivered_kwh cannot be negative")

# DELAY NOTIFICATION MODEL
@dataclass
class DelayNotification:
    reservation_id: str
    expected_arrival_iso: str
    updated_arrival_iso: str
    delay_minutes: float
    severity: DelaySeverity

    def __post_init__(self):
        if self.delay_minutes < 0:
            raise ValueError("delay_minutes cannot be negative")

# FAULT ALERT MODEL
@dataclass
class FaultAlert:
    reservation_id: str
    station_id: str
    fault_code: str
    description: str
    severity: FaultSeverity
    timestamp: datetime = field(default_factory=datetime.utcnow)

# SESSION RESULT MODEL
@dataclass
class SessionResult:
    reservation_id: str
    station_id: str
    user_id: str
    vehicle_id: str

    total_energy_kwh: float
    total_cost: float
    total_duration_min: float
    wait_time_min: float

    # Normalized scoring components (0–1)
    cost_score: float
    wait_score: float
    distance_score: float

    satisfaction: float  # 0–1 user satisfaction metric

    started_at: datetime
    completed_at: datetime

    def __post_init__(self):

        if self.total_energy_kwh < 0:
            raise ValueError("total_energy_kwh cannot be negative")

        if self.total_cost < 0:
            raise ValueError("total_cost cannot be negative")

        if self.total_duration_min < 0:
            raise ValueError("total_duration_min cannot be negative")

        if self.wait_time_min < 0:
            raise ValueError("wait_time_min cannot be negative")

        for field_name in ["cost_score", "wait_score", "distance_score", "satisfaction"]:
            value = getattr(self, field_name)
            if not (0 <= value <= 1):
                raise ValueError(f"{field_name} must be between 0 and 1")

    # SERIALIZATION
    def to_dict(self) -> dict:
        return {
            "reservation_id": self.reservation_id,
            "station_id": self.station_id,
            "user_id": self.user_id,
            "vehicle_id": self.vehicle_id,
            "total_energy_kwh": self.total_energy_kwh,
            "total_cost": self.total_cost,
            "total_duration_min": self.total_duration_min,
            "wait_time_min": self.wait_time_min,
            "cost_score": self.cost_score,
            "wait_score": self.wait_score,
            "distance_score": self.distance_score,
            "satisfaction": self.satisfaction,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
        }

    def __str__(self):
        return (
            f"SessionResult("
            f"reservation={self.reservation_id}, "
            f"station={self.station_id}, "
            f"cost={self.total_cost}, "
            f"satisfaction={self.satisfaction})"
        )

# ACTIVE SESSION TRACKER
@dataclass
class ChargingSession:
    reservation_id: str
    station_id: str
    status: SessionStatus = SessionStatus.INITIALIZED

    started_at: Optional[datetime] = None
    arrived_at: Optional[datetime] = None
    charging_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    latest_telemetry: Optional[TelemetryData] = None

    def mark_en_route(self):
        self.status = SessionStatus.EN_ROUTE

    def mark_arrived(self):
        self.status = SessionStatus.ARRIVED
        self.arrived_at = datetime.utcnow()

    def mark_charging_started(self):
        self.status = SessionStatus.CHARGING
        self.charging_started_at = datetime.utcnow()

    def mark_completed(self):
        self.status = SessionStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_failed(self):
        self.status = SessionStatus.FAILED

    def mark_cancelled(self):
        self.status = SessionStatus.CANCELLED