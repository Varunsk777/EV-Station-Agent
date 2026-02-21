import requests
import json
import time

from config.ua_config import UAConfig
from utils.logger import get_logger


class ServerSync:

    def __init__(self, local_cache):

        self.logger = get_logger("ServerSync")
        self.config = UAConfig()
        self.local_cache = local_cache
        self.base_url = self.config.server_base_url

    # PUSH WEIGHTS
    def push_weights(self, user_id, weight_dict):

        try:
            response = requests.post(
                f"{self.base_url}/save_weights",
                json=weight_dict,
                timeout=5,
            )
            response.raise_for_status()

        except Exception as e:
            self.logger.warning("Weight sync failed, enqueueing.")
            self.local_cache.enqueue_sync(
                "save_weights",
                weight_dict,
            )

    # PUSH SESSION
    def push_session(self, session_dict):

        try:
            response = requests.post(
                f"{self.base_url}/save_session",
                json=session_dict,
                timeout=5,
            )
            response.raise_for_status()

        except Exception:
            self.logger.warning("Session sync failed, enqueueing.")
            self.local_cache.enqueue_sync(
                "save_session",
                session_dict,
            )

    # PROCESS SYNC QUEUE
    def process_sync_queue(self):

        items = self.local_cache.get_pending_sync_items()

        for item_id, payload_json, endpoint in items:

            payload = json.loads(payload_json)

            try:
                response = requests.post(
                    f"{self.base_url}/{endpoint}",
                    json=payload,
                    timeout=5,
                )
                response.raise_for_status()

                self.local_cache.remove_sync_item(item_id)

            except Exception:
                self.logger.warning(
                    f"Retry failed for sync item {item_id}"
                )
                time.sleep(1)