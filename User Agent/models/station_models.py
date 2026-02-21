from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum

# ENUMS
class ChargerType(str, Enum):
    AC = "AC"
    DC_FAST = "DC_FAST"
    ULTRA_FAST = "ULTRA_FAST"


class StationStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    LIMITED = "LIMITED"
    FULL = "FULL"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"

# LOCATION MODEL
@dataclass(frozen=True)
class StationLocation:
    latitude: float
    longitude: float

    def as_tuple(self) -> Tuple[float, float]:
        return (self.latitude, self.longitude)

# MICRO SLOT MODEL
@dataclass(frozen=True)
class MicroSlot:
    slot_id: str
    start_time_iso: str
    end_time_iso: str
    price_modifier: float  # e.g., 0.9 for discount, 1.1 for surge

# STATION OPTION MODEL (FROM CA)
@dataclass(frozen=True)
class StationOption:
    station_id: str
    station_name: str
    operator_name: str

    location: StationLocation

    charger_type: ChargerType
    max_power_kw: float

    # CA-computed metrics
    distance_km: float
    estimated_travel_time_min: float
    estimated_wait_time_min: float
    estimated_price: float

    composite_score: float  # CA ranking score

    status: StationStatus

    available_slots: int

    micro_slots: List[MicroSlot] = field(default_factory=list)

    # VALIDATION
    def __post_init__(self):

        if self.distance_km < 0:
            raise ValueError("distance_km cannot be negative")

        if self.estimated_travel_time_min < 0:
            raise ValueError("estimated_travel_time_min cannot be negative")

        if self.estimated_wait_time_min < 0:
            raise ValueError("estimated_wait_time_min cannot be negative")

        if self.estimated_price < 0:
            raise ValueError("estimated_price cannot be negative")

        if self.max_power_kw <= 0:
            raise ValueError("max_power_kw must be positive")

        if self.available_slots < 0:
            raise ValueError("available_slots cannot be negative")


# RANKED STATION LIST (IMMUTABLE WRAPPER)
@dataclass(frozen=True)
class RankedStationList:
    stations: Tuple[StationOption, ...]

    def __post_init__(self):
        if not self.stations:
            raise ValueError("Ranked station list cannot be empty")

    def top(self) -> StationOption:
        return self.stations[0]

    def get_by_id(self, station_id: str) -> Optional[StationOption]:
        for station in self.stations:
            if station.station_id == station_id:
                return station
        return None

    def to_list(self) -> List[StationOption]:
        return list(self.stations)

    def __len__(self):
        return len(self.stations)

    def __iter__(self):
        return iter(self.stations)