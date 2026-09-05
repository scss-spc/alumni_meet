import os
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from config import Config
from services.sync_service import perform_sync, get_sync_status

logger = logging.getLogger(__name__)

_scheduler = None
_next_run_time: Optional[datetime] = None
_scheduler_lock = threading.Lock()
_fallback_timer: Optional[threading.Timer] = None

def _run_scheduled_job(app=None):
    """Execution wrapper for scheduled 24-hour sync job."""
    global _next_run_time
    logger.info("Executing scheduled 24-hour Google Sheet synchronization...")

    try:
        if app:
            with app.app_context():
                perform_sync(triggered_by="24h_scheduler")
        else:
            perform_sync(triggered_by="24h_scheduler")
    except Exception as e:
        logger.error(f"Scheduled sync job encountered an error: {e}", exc_info=True)
    finally:
        hours = Config.SYNC_INTERVAL_HOURS or 24
        _next_run_time = datetime.now() + timedelta(hours=hours)


def start_scheduler(app=None) -> bool:
    """
    Initialize and start the 24-hour background synchronization scheduler.
    Safe against Werkzeug dev reloader double invocation.
    """
    global _scheduler, _next_run_time, _fallback_timer

    # In Flask development mode, Werkzeug runs a child process with WERKZEUG_RUN_MAIN='true'.
    # Skip starting scheduler in parent process to avoid duplicate threads.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "false":
        logger.debug("Skipping scheduler initialization in Werkzeug parent process.")
        return False

    if not Config.AUTO_SYNC_ENABLED:
        logger.info("Auto-sync is disabled via configuration (AUTO_SYNC_ENABLED=False).")
        return False

    with _scheduler_lock:
        if _scheduler is not None or _fallback_timer is not None:
            logger.info("Sync scheduler is already running.")
            return True

        hours = Config.SYNC_INTERVAL_HOURS or 24
        _next_run_time = datetime.now() + timedelta(hours=hours)

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.interval import IntervalTrigger

            scheduler = BackgroundScheduler(daemon=True)
            scheduler.add_job(
                func=_run_scheduled_job,
                args=[app],
                trigger=IntervalTrigger(hours=hours),
                id="google_sheet_24h_sync",
                name="24-Hour Google Sheet Sync",
                replace_existing=True
            )
            scheduler.start()
            _scheduler = scheduler
            logger.info(f"APScheduler started successfully: Syncing every {hours} hours (Next run: {_next_run_time})")
            return True

        except Exception as e:
            logger.warning(f"APScheduler failed to start ({e}); falling back to threading.Timer daemon.")
            
            def _timer_loop():
                global _fallback_timer
                _run_scheduled_job(app)
                interval_seconds = hours * 3600
                _fallback_timer = threading.Timer(interval_seconds, _timer_loop)
                _fallback_timer.daemon = True
                _fallback_timer.start()

            interval_seconds = hours * 3600
            _fallback_timer = threading.Timer(interval_seconds, _timer_loop)
            _fallback_timer.daemon = True
            _fallback_timer.start()
            logger.info(f"Fallback threading timer started: Interval {hours} hours.")
            return True


def stop_scheduler():
    """Cleanly stop background scheduler and timers."""
    global _scheduler, _fallback_timer, _next_run_time
    with _scheduler_lock:
        if _scheduler:
            try:
                _scheduler.shutdown(wait=False)
            except Exception as e:
                logger.warning(f"Error shutting down APScheduler: {e}")
            _scheduler = None

        if _fallback_timer:
            _fallback_timer.cancel()
            _fallback_timer = None

        _next_run_time = None
        logger.info("Sync scheduler stopped.")


def get_scheduler_info() -> Dict[str, Any]:
    """Retrieve scheduler configuration and next scheduled run time."""
    is_active = (_scheduler is not None and _scheduler.running) or (_fallback_timer is not None)
    hours = Config.SYNC_INTERVAL_HOURS or 24

    return {
        "auto_sync_enabled": Config.AUTO_SYNC_ENABLED,
        "is_active": is_active,
        "interval_hours": hours,
        "sheet_id_configured": bool(Config.GOOGLE_SHEET_ID or Config.GOOGLE_SHEET_CSV_URL),
        "sheet_id": Config.GOOGLE_SHEET_ID or Config.GOOGLE_SHEET_CSV_URL or "Not Configured",
        "next_run_time": _next_run_time.strftime("%Y-%m-%d %H:%M:%S") if _next_run_time else None
    }
