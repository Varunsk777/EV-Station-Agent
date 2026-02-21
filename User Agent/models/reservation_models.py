from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

# ENUMS
class ReservationStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
    FAILED = "FAILED"


class CancellationReason(str, Enum):
    USER_CANCELLED = "USER_CANCELLED"
    DELAY = "DELAY"
    FAULT = "FAULT"
    NO_SHOW = "NO_SHOW"
    SYSTEM = "SYSTEM"

# RESERVATION MODEL
@dataclass
class Reservation:
    reservation_id: str
    station_id: str
    user_id: str
    vehicle_id: str

    # Slot details
    slot_id: str
    slot_start_time_iso: str
    slot_end_time_iso: str

    # Pricing
    reserved_price: float

    # Status
    status: ReservationStatus = ReservationStatus.CONFIRMED

    # Timing metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    cancellation_reason: Optional[CancellationReason] = None

    # VALIDATION
    def __post_init__(self):

        if self.reserved_price < 0:
            raise ValueError("reserved_price cannot be negative")

        if not self.reservation_id:
            raise ValueError("reservation_id required")

        if not self.station_id:
            raise ValueError("station_id required")

        if not self.slot_id:
            raise ValueError("slot_id required")

    # STATE TRANSITIONS
    def mark_active(self):
        if self.status != ReservationStatus.CONFIRMED:
            raise ValueError("Only CONFIRMED reservation can become ACTIVE")

        self.status = ReservationStatus.ACTIVE
        self.activated_at = datetime.utcnow()

    def mark_completed(self):
        if self.status != ReservationStatus.ACTIVE:
            raise ValueError("Only ACTIVE reservation can be completed")

        self.status = ReservationStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_cancelled(self, reason: CancellationReason):
        if self.status in (
            ReservationStatus.COMPLETED,
            ReservationStatus.CANCELLED,
        ):
            raise ValueError("Reservation already finalized")

        self.status = ReservationStatus.CANCELLED
        self.cancellation_reason = reason
        self.cancelled_at = datetime.utcnow()

    def mark_no_show(self):
        if self.status != ReservationStatus.CONFIRMED:
            raise ValueError("Only CONFIRMED reservation can be NO_SHOW")

        self.status = ReservationStatus.NO_SHOW
        self.cancelled_at = datetime.utcnow()

    # SERIALIZATION
    def to_dict(self) -> dict:
        return {
            "reservation_id": self.reservation_id,
            "station_id": self.station_id,
            "user_id": self.user_id,
            "vehicle_id": self.vehicle_id,
            "slot_id": self.slot_id,
            "slot_start_time_iso": self.slot_start_time_iso,
            "slot_end_time_iso": self.slot_end_time_iso,
            "reserved_price": self.reserved_price,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "activated_at": self.activated_at.isoformat()
            if self.activated_at
            else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "cancelled_at": self.cancelled_at.isoformat()
            if self.cancelled_at
            else None,
            "cancellation_reason": self.cancellation_reason.value
            if self.cancellation_reason
            else None,
        }

    # DEBUG STRING
    def __str__(self):
        return (
            f"Reservation("
            f"id={self.reservation_id}, "
            f"station={self.station_id}, "
            f"status={self.status.value})"
        )