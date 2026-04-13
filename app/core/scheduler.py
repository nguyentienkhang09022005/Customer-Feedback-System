import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.core.config import settings
from app.db.session import SessionLocal
from app.core.jobs import run_survey_job

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def survey_job_wrapper():
    """Wrapper to create DB session for APScheduler job"""
    logger.info("[SurveyJob] Starting survey check...")
    db = SessionLocal()
    try:
        result = run_survey_job(db)
        logger.info(f"[SurveyJob] Completed: {result}")
    except Exception as e:
        logger.error(f"[SurveyJob] Error: {e}", exc_info=True)
    finally:
        db.close()


def init_scheduler():
    """Initialize and start the APScheduler"""
    scheduler.add_job(
        survey_job_wrapper,
        trigger=IntervalTrigger(hours=settings.SURVEY_JOB_INTERVAL_HOURS),
        id="survey_job",
        replace_existing=True,
        max_instances=1
    )
    scheduler.start()
    logger.info(f"[Scheduler] Started - Survey job runs every {settings.SURVEY_JOB_INTERVAL_HOURS} hour(s)")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    scheduler.shutdown(wait=False)
    logger.info("[Scheduler] Shutdown complete")
