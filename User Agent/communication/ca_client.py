import requests
import time
from typing import List
from dataclasses import asdict

from config.ua_config import UAConfig
from utils.logger import get_logger
from communication.messaging_protocol import (
    ChargingRequest,
    StationSelectionDecision,
    SlotCancellationRequest,
    DelayReport,
)


class CAClient:

    def __init__(self):

        self.logger = get_logger("CAClient")
        self.config = UAConfig()
        self.base_url = self.config.ca_base_url

    # INTERNAL RETRY LOGIC

    def _post_with_retry(self, endpoint: str, payload: dict):

        retries = self.config.max_retries
        delay = self.config.initial_retry_delay

        for attempt in range(retries):

            try:
                response = requests.post(
                    f"{self.base_url}/{endpoint}",
                    json=payload,
                    timeout=self.config.ca_timeout_sec,
                )

                response.raise_for_status()
                return response.json()

            except Exception as e:
                self.logger.warning(
                    f"CA request failed (attempt {attempt+1}): {e}"
                )
                time.sleep(delay)
                delay *= 2

        raise Exception("CA unreachable after retries")

    # CHARGING REQUEST

    def send_charging_request(
        self,
        vehicle_context: dict,
        preference_params: dict,
        urgency_level: str,
    ) -> List[dict]:

        request = ChargingRequest(
            vehicle_context=vehicle_context,
            preference_params=preference_params,
            urgency_level=urgency_level,
        )

        response = self._post_with_retry(
            "charging_request",
            asdict(request),
        )

        return response.get("stations", [])

    # CONFIRM STATION

    def confirm_station_selection(self, station_id: str):

        decision = StationSelectionDecision(station_id=station_id)

        response = self._post_with_retry(
            "confirm_station",
            asdict(decision),
        )

        return response

    # SLOT CANCELLATION

    def request_slot_cancellation(self, reservation_id: str, reason: str):

        request = SlotCancellationRequest(
            reservation_id=reservation_id,
            reason=reason,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
        )

        return self._post_with_retry(
            "cancel_reservation",
            asdict(request),
        )

    # DELAY REPORT (COPY TO CA)

    def send_delay_report(self, delay_result):

        report = DelayReport(
            reservation_id=delay_result.reservation_id,
            new_eta=delay_result.new_eta,
            delay_minutes=delay_result.delay_minutes,
            severity=delay_result.severity,
        )

        return self._post_with_retry(
            "delay_report",
            asdict(report),
        )