from dataclasses import dataclass
from typing import List, Optional


# UA → CA

@dataclass
class ChargingRequest:
    vehicle_context: dict
    preference_params: dict
    urgency_level: str


@dataclass
class StationSelectionDecision:
    station_id: str


@dataclass
class SlotCancellationRequest:
    reservation_id: str
    reason: str
    timestamp: str


@dataclass
class DelayReport:
    reservation_id: str
    new_eta: str
    delay_minutes: int
    severity: str


# CA → UA

@dataclass
class RankedStationList:
    stations: List[dict]


@dataclass
class ReservationConfirmation:
    reservation_id: str
    station_id: str
    slot_id: str
    start_time: str
    duration_min: int


# UA → SA (LIMITED CHANNEL)

@dataclass
class DelayNotification:
    reservation_id: str
    new_eta: str
    delay_minutes: int
    reason_code: str


@dataclass
class MicroSlotDecision:
    micro_slot_id: str
    decision: str
    vehicle_id: str


# SA → UA
@dataclass
class MicroSlotOffer:
    micro_slot_id: str
    available_window_start: str
    available_window_end: str
    station_id: str


@dataclass
class SessionTelemetry:
    charging_progress_pct: float
    power_kw: float
    energy_kwh: float
    session_status: str
    timestamp: str


@dataclass
class FaultAlert:
    fault_type: str
    severity: str
    station_id: str
    slot_id: str
    timestamp: str