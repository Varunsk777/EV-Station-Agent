CREATE_TABLES_SQL = [

    # Preference weights (latest only)
    """
    CREATE TABLE IF NOT EXISTS preference_weights (
        user_id TEXT PRIMARY KEY,
        w_cost REAL,
        w_wait REAL,
        w_distance REAL,
        last_updated TEXT
    );
    """,

    # Explicit user preferences
    """
    CREATE TABLE IF NOT EXISTS explicit_preferences (
        user_id TEXT PRIMARY KEY,
        max_cost REAL,
        max_wait INTEGER,
        max_distance REAL,
        last_updated TEXT
    );
    """,

    # Session history (local copy)
    """
    CREATE TABLE IF NOT EXISTS session_history (
        session_id TEXT PRIMARY KEY,
        reservation_id TEXT,
        station_id TEXT,
        actual_cost REAL,
        actual_wait_min INTEGER,
        distance_km REAL,
        energy_delivered_kwh REAL,
        session_start TEXT,
        session_end TEXT,
        user_satisfaction INTEGER
    );
    """,

    # Pending sync queue
    """
    CREATE TABLE IF NOT EXISTS sync_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payload TEXT,
        endpoint TEXT,
        created_at TEXT
    );
    """
]
