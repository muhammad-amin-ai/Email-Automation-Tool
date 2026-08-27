import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.database.connection import SessionLocal
from app.services.campaign_service import process_due_jobs


logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _run_due_jobs_tick() -> None:
    """One scheduler tick: open a DB session, process a batch of due jobs, close it.

    This is what makes delayed / drip campaign steps actually fire without
    anyone having to manually re-open the campaign. Runs every
    SCHEDULER_INTERVAL_SECONDS in a background thread inside the API process.
    """
    db = SessionLocal()
    try:
        processed = process_due_jobs(db, limit=settings.SCHEDULER_BATCH_SIZE)
        if processed:
            logger.info(f"Scheduler tick: processed {processed} due email job(s).")
    except Exception as e:
        logger.exception(f"Scheduler tick failed: {e}")
    finally:
        db.close()


def start_scheduler() -> None:
    global _scheduler

    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler disabled via SCHEDULER_ENABLED=false.")
        return

    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        _run_due_jobs_tick,
        "interval",
        seconds=settings.SCHEDULER_INTERVAL_SECONDS,
        id="process_due_email_jobs",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info(
        f"Scheduler started: checking for due email jobs every "
        f"{settings.SCHEDULER_INTERVAL_SECONDS}s."
    )


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped.")