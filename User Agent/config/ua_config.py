class UAConfig:

    # GENERAL SYSTEM CONFIG
    poll_interval_sec = 5                # Orchestrator loop interval
    error_retry_delay_sec = 3            # Retry delay after system error
    enable_scheduled_trigger = False     # Enable calendar-based trigger
    debug_mode = True

    # CONTEXT MANAGER CONFIG

    # SoC thresholds (fractions 0.0–1.0)
    soc_emergency_threshold = 0.10       # <= 10%
    soc_high_threshold = 0.25            # 10%–25%
    soc_medium_threshold = 0.50          # 25%–50%
    soc_trigger_threshold = 0.30         # Trigger search threshold

    # PREFERENCE MANAGER CONFIG
    learning_rate = 0.05                 # Adaptive update strength
    minimum_weight_floor = 0.05          # Prevent weight collapse
    max_weight_cap = 0.90                # Optional safety cap

    # SESSION MONITOR CONFIG
    
    # Delay policy thresholds (minutes)
    minor_delay_threshold_min = 5
    major_delay_threshold_min = 15
    no_show_threshold_min = 30

    # Telemetry handling
    telemetry_timeout_sec = 60

    # ETA estimation
    default_avg_speed_kmph = 40

    # CA (Coordinator Agent) CONFIG
    ca_base_url = "http://localhost:8000/ca"
    ca_timeout_sec = 5

    # Retry policy for CA communication
    max_retries = 3
    initial_retry_delay = 1

    # SA (Station Agent) CONFIG
    sa_base_url = "http://localhost:8001/sa"
    sa_timeout_sec = 5

    # SERVER SYNC CONFIG (Long-Term Storage)
    server_base_url = "http://localhost:9000/api"
    server_timeout_sec = 5
    sync_retry_interval_sec = 10


    # DATABASE CONFIG
    local_db_path = "ua_local.db"

    # SAFETY & POLICY FLAGS
    enforce_no_rerank_rule = True        # UA must not re-rank stations
    allow_micro_slot_direct = True       # Allow direct SA micro-slot comms
    allow_delay_direct_to_sa = True      # Minor delays sent directly

    # LOGGING CONFIG
    log_level = "INFO"
    enable_structured_logging = True