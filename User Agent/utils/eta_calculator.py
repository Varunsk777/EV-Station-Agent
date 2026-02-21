from datetime import datetime
from math import radians, sin, cos, sqrt, atan2


class ETACalculator:
    EARTH_RADIUS_KM = 6371.0

    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)

        a = (
            sin(dlat / 2) ** 2
            + cos(radians(lat1))
            * cos(radians(lat2))
            * sin(dlon / 2) ** 2
        )

        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return ETACalculator.EARTH_RADIUS_KM * c

    @staticmethod
    def estimate_eta_minutes(
        current_lat,
        current_lon,
        target_lat,
        target_lon,
        avg_speed_kmh=40,
    ):
        distance_km = ETACalculator.haversine_distance(
            current_lat, current_lon, target_lat, target_lon
        )

        if avg_speed_kmh <= 0:
            raise ValueError("avg_speed_kmh must be positive")

        hours = distance_km / avg_speed_kmh
        return hours * 60

    @staticmethod
    def compute_delay_minutes(
        expected_arrival: datetime,
        new_arrival: datetime,
    ) -> float:
        delta = new_arrival - expected_arrival
        return max(delta.total_seconds() / 60, 0)