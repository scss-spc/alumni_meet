import json
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List

from config import Config
from services.sheets_service import GoogleSheetsConnector
from db.alumni import get_alumnus_by_email, create_alumnus, update_alumnus
from db.meets import save_meet_response, get_active_meet
from db.contributions import (
    create_contribution,
    get_contribution_by_reference,
    get_existing_contribution_for_sync,
    save_recognition_preference
)
from db.audit import log_audit_action

logger = logging.getLogger(__name__)

# Thread-safe sync state tracker
_sync_lock = threading.Lock()
_sync_state: Dict[str, Any] = {
    "last_sync_time": None,
    "status": "IDLE",  # IDLE, RUNNING, SUCCESS, ERROR
    "message": "No sync performed yet in this session.",
    "is_syncing": False,
    "metrics": {
        "total_rows": 0,
        "alumni_created": 0,
        "alumni_updated": 0,
        "responses_synced": 0,
        "contributions_logged": 0,
        "errors_count": 0,
    },
    "column_mapping": {},
    "last_error": None
}

def get_sync_status() -> Dict[str, Any]:
    """Retrieve current synchronization status and telemetry."""
    with _sync_lock:
        return dict(_sync_state)

def test_sheet_connection() -> Dict[str, Any]:
    """
    Test connectivity to the configured Google Sheet without writing to DB.
    Returns connection diagnosis, row count, and detected column mapping.
    """
    connector = GoogleSheetsConnector(
        sheet_id=Config.GOOGLE_SHEET_ID,
        sheet_name=Config.GOOGLE_SHEET_NAME,
        csv_url=Config.GOOGLE_SHEET_CSV_URL,
        service_account_file=Config.GOOGLE_SERVICE_ACCOUNT_FILE,
        service_account_json=Config.GOOGLE_SERVICE_ACCOUNT_JSON
    )

    try:
        records, col_map = connector.fetch_and_normalize()
        return {
            "success": True,
            "message": f"Successfully connected to Google Sheet. Found {len(records)} valid response rows.",
            "total_records": len(records),
            "column_mapping": col_map,
            "sample": records[:2] if records else []
        }
    except Exception as e:
        logger.error(f"Sheet connection test failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "sheet_id": Config.GOOGLE_SHEET_ID,
            "has_service_account": bool(Config.GOOGLE_SERVICE_ACCOUNT_FILE or Config.GOOGLE_SERVICE_ACCOUNT_JSON)
        }

def perform_sync(
    meet_id: Optional[int] = None,
    triggered_by: str = "scheduler",
    user_id: Optional[int] = None,
    records_override: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Execute full sync pipeline from Google Sheet responses into the database.
    Thread-safe and atomic per-alumnus.
    """
    global _sync_state

    # Acquire lock or return if sync is already running
    if not _sync_lock.acquire(blocking=False):
        return {
            "success": False,
            "error": "A synchronization process is already in progress.",
            "status": "RUNNING"
        }

    try:
        _sync_state["is_syncing"] = True
        _sync_state["status"] = "RUNNING"
        _sync_state["message"] = f"Synchronization started (Trigger: {triggered_by})..."
        _sync_state["last_error"] = None

        target_meet_id = meet_id or Config.CURRENT_MEET_ID
        active_meet = get_active_meet()
        if active_meet and not meet_id:
            target_meet_id = active_meet["id"]

        logger.info(f"Starting Google Sheet Sync for Meet ID {target_meet_id} (Trigger: {triggered_by})")

        # Step 1: Fetch and normalize records
        if records_override is not None:
            records = records_override
            col_map = {"custom_records": "provided"}
        else:
            connector = GoogleSheetsConnector(
                sheet_id=Config.GOOGLE_SHEET_ID,
                sheet_name=Config.GOOGLE_SHEET_NAME,
                csv_url=Config.GOOGLE_SHEET_CSV_URL,
                service_account_file=Config.GOOGLE_SERVICE_ACCOUNT_FILE,
                service_account_json=Config.GOOGLE_SERVICE_ACCOUNT_JSON
            )
            records, col_map = connector.fetch_and_normalize()

        metrics = {
            "total_rows": len(records),
            "alumni_created": 0,
            "alumni_updated": 0,
            "responses_synced": 0,
            "contributions_logged": 0,
            "errors_count": 0
        }
        row_errors: List[Dict[str, Any]] = []

        # Step 2: Ingest each record into database
        for rec in records:
            row_num = rec.get("row_number", "?")
            try:
                email = rec["email"]
                existing_alumnus = get_alumnus_by_email(email)

                if existing_alumnus:
                    alumni_id = existing_alumnus["id"]
                    # Merge update: update fields if provided in sheet
                    update_payload = {
                        "full_name": rec.get("full_name") or existing_alumnus.get("full_name"),
                        "graduation_year": rec.get("graduation_year") or existing_alumnus.get("graduation_year"),
                        "course": rec.get("course") or existing_alumnus.get("course"),
                        "phone": rec.get("phone") or existing_alumnus.get("phone"),
                        "organization": rec.get("organization") or existing_alumnus.get("organization"),
                        "designation": rec.get("designation") or existing_alumnus.get("designation"),
                        "current_location": rec.get("current_location") or existing_alumnus.get("current_location")
                    }
                    update_alumnus(alumni_id, update_payload)
                    metrics["alumni_updated"] += 1
                else:
                    alumni_id = create_alumnus(rec)
                    metrics["alumni_created"] += 1

                # Save Meet Response
                response_payload = {
                    "meet_id": target_meet_id,
                    "alumni_id": alumni_id,
                    "attending": rec.get("attending", True),
                    "guest_count": rec.get("guest_count", 0),
                    "total_attendees": rec.get("total_attendees", 1),
                    "dietary_preferences": rec.get("dietary_preferences"),
                    "suggestions": rec.get("suggestions")
                }
                save_meet_response(response_payload)
                metrics["responses_synced"] += 1

                # Save Contribution if amount or reference provided
                amount = rec.get("amount", 0.0)
                tx_ref = rec.get("transaction_reference")
                screenshot = rec.get("payment_screenshot_path")

                if amount > 0 or tx_ref or screenshot:
                    # Intelligently check for duplicate contribution across reference, screenshot, or alumnus
                    existing_contrib = get_existing_contribution_for_sync(
                        meet_id=target_meet_id,
                        alumni_id=alumni_id,
                        tx_ref=tx_ref,
                        screenshot=screenshot,
                        amount=amount
                    )
                    if not existing_contrib:
                        contrib_payload = {
                            "meet_id": target_meet_id,
                            "alumni_id": alumni_id,
                            "amount": amount,
                            "currency": "INR",
                            "transaction_reference": tx_ref,
                            "payment_screenshot_path": screenshot,
                            "payment_status": "submitted",
                            "notes": f"Auto-synced from Google Sheet (Row {row_num})"
                        }
                        create_contribution(contrib_payload)
                        metrics["contributions_logged"] += 1

                # Save Public Recognition Preference
                save_recognition_preference(target_meet_id, alumni_id, rec.get("recognition_type", "name_only"))

            except Exception as e:
                logger.error(f"Error processing row {row_num} for email {rec.get('email')}: {e}")
                metrics["errors_count"] += 1
                row_errors.append({"row": row_num, "email": rec.get("email"), "error": str(e)})

        # Log audit trail
        sync_summary_str = json.dumps({
            "trigger": triggered_by,
            "metrics": metrics,
            "row_errors": row_errors[:5]  # limit error payload size
        })
        try:
            log_audit_action(
                action="google_sheet_sync",
                entity_type="google_sheet",
                entity_id=target_meet_id,
                user_id=user_id,
                new_value=sync_summary_str
            )
        except Exception as audit_err:
            logger.warning(f"Could not write audit log for sync: {audit_err}")

        # Update telemetry
        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _sync_state["last_sync_time"] = now_iso
        _sync_state["status"] = "SUCCESS" if metrics["errors_count"] == 0 else "PARTIAL_SUCCESS"
        _sync_state["message"] = (
            f"Synced {metrics['total_rows']} responses ({metrics['alumni_created']} new alumni, "
            f"{metrics['alumni_updated']} updated, {metrics['contributions_logged']} contributions)."
        )
        _sync_state["metrics"] = metrics
        _sync_state["column_mapping"] = col_map
        _sync_state["row_errors"] = row_errors

        logger.info(f"Sync complete: {_sync_state['message']}")
        return {
            "success": True,
            "message": _sync_state["message"],
            "metrics": metrics,
            "column_mapping": col_map,
            "row_errors": row_errors
        }

    except Exception as e:
        logger.error(f"Sync failed with unhandled exception: {e}", exc_info=True)
        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _sync_state["last_sync_time"] = now_iso
        _sync_state["status"] = "ERROR"
        _sync_state["message"] = f"Sync failed: {str(e)}"
        _sync_state["last_error"] = str(e)
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        _sync_state["is_syncing"] = False
        _sync_lock.release()
