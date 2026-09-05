"""
Standalone CLI script for synchronizing alumni responses from Google Sheets into the database.
Can be executed manually or scheduled via Windows Task Scheduler / Cron.

Usage:
    python sync_job.py          # Run full sync
    python sync_job.py --test   # Test connection to Google Sheet without writing to DB
    python sync_job.py --purge  # Purge all alumni data and re-sync from Google Sheet
"""

import sys
import json
import logging
from services.sync_service import perform_sync, test_sheet_connection
from services.alumni_service import purge_all_alumni_records

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sync_job")

def main():
    if "--test" in sys.argv or "-t" in sys.argv:
        logger.info("Testing Google Sheet connection...")
        result = test_sheet_connection()
        print("\n--- Google Sheet Connection Test ---")
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("success") else 1)

    if "--purge" in sys.argv or "--purge-all" in sys.argv or "-p" in sys.argv:
        logger.warning("Purging all existing alumni data prior to sync...")
        metrics = purge_all_alumni_records()
        print(f"Purge complete: {metrics['alumni_deleted']} alumni, {metrics['contributions_deleted']} contributions, {metrics['responses_deleted']} responses deleted.")

    logger.info("Executing Google Sheet to Database Synchronization...")
    result = perform_sync(triggered_by="cli_sync_job")
    print("\n--- Sync Execution Summary ---")
    print(json.dumps(result, indent=2))
    
    if result.get("success"):
        logger.info("Synchronization completed successfully.")
        sys.exit(0)
    else:
        logger.error(f"Synchronization failed: {result.get('error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
