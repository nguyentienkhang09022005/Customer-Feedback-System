import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from app.core.config import settings
from app.db.session import SessionLocal
from app.core.jobs import run_survey_job, run_sentiment_analysis

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

SENTIMENT_JOB_INTERVAL_DAYS = 7


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


def sentiment_job_wrapper():
    """Wrapper to create DB session for Sentiment Analysis job"""
    logger.info("[SentimentJob] Starting sentiment analysis...")
    db = SessionLocal()
    try:
        result = run_sentiment_analysis(db)
        logger.info(f"[SentimentJob] Completed: {result}")
    except Exception as e:
        logger.error(f"[SentimentJob] Error: {e}", exc_info=True)
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

    scheduler.add_job(
        sentiment_job_wrapper,
        trigger=CronTrigger(day_of_week="mon", hour=2, minute=0),
        id="sentiment_analysis_job",
        replace_existing=True,
        max_instances=1
    )

    scheduler.start()
    logger.info(f"[Scheduler] Started - Survey job runs every {settings.SURVEY_JOB_INTERVAL_HOURS} hour(s)")
    logger.info(f"[Scheduler] Sentiment job runs every {SENTIMENT_JOB_INTERVAL_DAYS} days (Monday 2am)")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    scheduler.shutdown(wait=False)
    logger.info("[Scheduler] Shutdown complete")
