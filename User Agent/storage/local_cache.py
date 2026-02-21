import sqlite3
import json
from datetime import datetime
from typing import Optional

from storage.database_schema import CREATE_TABLES_SQL
from utils.logger import get_logger


class LocalCache:

    def __init__(self, db_path: str = "ua_local.db"):

        self.logger = get_logger("LocalCache")

        # In-memory fields
        self.current_vehicle_context = None
        self.active_reservation = None
        self.ranked_stations_cache = None
        self.current_session_telemetry = None
        self.expected_arrival_time = None
        self.pending_micro_slot_offer = None
        self.session_result = None

        # DB connection
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._initialize_schema()

        self.logger.info("LocalCache initialized.")

    # DB INIT
    def _initialize_schema(self):
        cursor = self.conn.cursor()
        for query in CREATE_TABLES_SQL:
            cursor.execute(query)
        self.conn.commit()

    # SESSION HISTORY
    def save_session(self, session_dict: dict):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO session_history
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_dict["session_id"],
            session_dict["reservation_id"],
            session_dict["station_id"],
            session_dict["actual_cost"],
            session_dict["actual_wait_min"],
            session_dict["distance_km"],
            session_dict["energy_delivered_kwh"],
            session_dict["session_start"],
            session_dict["session_end"],
            session_dict["user_satisfaction"],
        ))
        self.conn.commit()

    # PREFERENCE CACHE
    def save_preference_weights(self, user_id, w_cost, w_wait, w_distance):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO preference_weights
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            w_cost,
            w_wait,
            w_distance,
            datetime.utcnow().isoformat(),
        ))
        self.conn.commit()

    # SYNC QUEUE
    def enqueue_sync(self, endpoint: str, payload: dict):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sync_queue (payload, endpoint, created_at)
            VALUES (?, ?, ?)
        """, (
            json.dumps(payload),
            endpoint,
            datetime.utcnow().isoformat(),
        ))
        self.conn.commit()

    def get_pending_sync_items(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, payload, endpoint FROM sync_queue")
        return cursor.fetchall()

    def remove_sync_item(self, item_id: int):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM sync_queue WHERE id=?", (item_id,))
        self.conn.commit()

    # CLEAR SESSION MEMORY
    def clear_session_data(self):

        self.active_reservation = None
        self.current_session_telemetry = None
        self.expected_arrival_time = None
        self.pending_micro_slot_offer = None
        self.session_result = None

        self.logger.info("Session memory cleared.")