import requests
from dataclasses import asdict

from config.ua_config import UAConfig
from utils.logger import get_logger
from communication.messaging_protocol import (
    DelayNotification,
    MicroSlotDecision,
)


class SAClient:

    def __init__(self):

        self.logger = get_logger("SAClient")
        self.config = UAConfig()
        self.base_url = self.config.sa_base_url

    # DELAY NOTIFICATION

    def send_delay_notification(
        self,
        reservation_id: str,
        new_eta: str,
        delay_minutes: int,
        reason_code: str,
    ):

        notification = DelayNotification(
            reservation_id=reservation_id,
            new_eta=new_eta,
            delay_minutes=delay_minutes,
            reason_code=reason_code,
        )

        try:
            response = requests.post(
                f"{self.base_url}/delay_notification",
                json=asdict(notification),
                timeout=self.config.sa_timeout_sec,
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            self.logger.error(f"Failed to send delay notification: {e}")
            raise

    # MICRO-SLOT DECISION

    def send_micro_slot_decision(
        self,
        micro_slot_id: str,
        decision: str,
        vehicle_id: str,
    ):

        payload = MicroSlotDecision(
            micro_slot_id=micro_slot_id,
            decision=decision,
            vehicle_id=vehicle_id,
        )

        try:
            response = requests.post(
                f"{self.base_url}/micro_slot_decision",
                json=asdict(payload),
                timeout=self.config.sa_timeout_sec,
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            self.logger.error(f"Failed to send micro-slot decision: {e}")
            raise