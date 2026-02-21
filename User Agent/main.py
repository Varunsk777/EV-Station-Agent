import threading
import time
import signal
import sys
from datetime import datetime

from orchestrator.ua_orchestrator import UAOrchestrator
from storage.local_cache import LocalCache
from storage.server_sync import ServerSync
from config.ua_config import UAConfig
from utils.logger import get_logger


# GLOBALS
logger = get_logger("UA_Main")
config = UAConfig()

running = True


# BACKGROUND SYNC WORKER
def sync_worker(server_sync: ServerSync):
    logger.info("Starting background sync worker.")

    while running:
        try:
            server_sync.process_sync_queue()
            time.sleep(config.sync_retry_interval_sec)

        except Exception as e:
            logger.error(f"Sync worker error: {e}")
            time.sleep(5)


# GPS SIMULATION (Demo Mode)
def gps_simulation_worker(orchestrator: UAOrchestrator):
    logger.info("Starting GPS simulation worker.")

    while running:
        try:
            gps_data = {
                "lat": 12.9716,
                "lon": 77.5946,
            }

            orchestrator.process_delay_update(gps_data)
            time.sleep(10)

        except Exception as e:
            logger.error(f"GPS simulation error: {e}")
            time.sleep(5)


# SHUTDOWN
def shutdown_handler(sig, frame):
    global running
    logger.info("Shutdown signal received. Stopping UA...")
    running = False
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)


# MAIN FUNCTION
def main():

    logger.info("Initializing User Agent System...")

    # Initialize local cache
    local_cache = LocalCache(config.local_db_path)

    # Initialize orchestrator
    orchestrator = UAOrchestrator(
        user_id="user_001",
        vehicle_id="vehicle_001"
    )

    # Initialize server sync
    server_sync = ServerSync(local_cache)

    # Start UA Orchestrator in separate thread
    ua_thread = threading.Thread(
        target=orchestrator.start,
        daemon=True
    )
    ua_thread.start()

    # Start sync worker
    sync_thread = threading.Thread(
        target=sync_worker,
        args=(server_sync,),
        daemon=True
    )
    sync_thread.start()

    # Start GPS simulation worker
    gps_thread = threading.Thread(
        target=gps_simulation_worker,
        args=(orchestrator,),
        daemon=True
    )
    gps_thread.start()

    logger.info("User Agent is running.")

    # Keep main thread alive
    while running:
        time.sleep(1)


if __name__ == "__main__":
    main()