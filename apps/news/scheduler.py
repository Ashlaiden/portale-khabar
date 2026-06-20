"""
Background scheduler for automatic RSS fetching.

We use ``django-apscheduler`` (a thin wrapper around APScheduler) so the
scheduler lives inside the Django process — no Celery, no Redis, no separate
worker. Job executions are persisted to the database and visible in the admin
under "Django Job Execution".

A single interval job, ``fetch_all_due_feeds_job``, runs every few minutes and
imports any feed whose individual interval has elapsed (see
RSSFeed.is_due). This keeps the schedule simple while still allowing per-feed
polling intervals.
"""

import atexit
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobExecution

logger = logging.getLogger(__name__)

# The master tick interval. The actual per-feed intervals are enforced inside
# the job via ``RSSFeed.is_due``, so this only needs to be "fine-grained enough"
# (e.g. 5 minutes). Setting it lower wastes CPU; higher means slower reaction.
MASTER_INTERVAL_SECONDS = 5 * 60

# Singleton scheduler instance; created on first start().
_scheduler = None


def fetch_all_due_feeds_job():
    """
    Scheduled job: pull every active RSS feed that is currently due.

    Wrapped in its own function (rather than registered directly) so the job
    name shown in the admin is readable and we can log results centrally.
    """
    from .services import rss_fetcher

    logger.info('Scheduler tick: fetching due RSS feeds…')
    try:
        results = rss_fetcher.fetch_all_due_feeds()
    except Exception:  # pragma: no cover - defensive
        logger.exception('Scheduled RSS fetch crashed.')
        return

    if results:
        logger.info('Scheduler tick done: %s', results)
    else:
        logger.info('Scheduler tick done: no feeds were due.')


def start():
    """
    Initialise and start the background scheduler (idempotent).

    Safe to call multiple times: a second call is a no-op. The scheduler is
    shut down automatically on process exit via ``atexit``.
    """
    global _scheduler
    if _scheduler is not None:
        # Already started (e.g. ready() fired twice in some setups).
        return _scheduler

    scheduler = BackgroundScheduler(timezone='Asia/Tehran')

    # Register the master tick job. ``replace_existing=True`` keeps the job
    # entry stable across reloads (no duplicate rows in DjangoJob).
    scheduler.add_job(
        fetch_all_due_feeds_job,
        trigger='interval',
        seconds=MASTER_INTERVAL_SECONDS,
        id='fetch_all_due_feeds',
        replace_existing=True,
    )

    try:
        scheduler.start()
        logger.info('Background scheduler started (every %ds).', MASTER_INTERVAL_SECONDS)
    except Exception:  # pragma: no cover - defensive
        logger.exception('Could not start the background scheduler.')
        return None

    # Tidy up old job-execution rows so the table doesn't grow forever.
    # In django-apscheduler >= 0.7 the helper takes ``max_age`` in *seconds*.
    try:
        DjangoJobExecution.objects.delete_old_job_executions(max_age=48 * 60 * 60)
    except Exception:  # pragma: no cover
        logger.exception('Could not prune old job executions.')

    _scheduler = scheduler
    atexit.register(lambda: _shutdown(scheduler))
    return scheduler


def _shutdown(scheduler):
    """Gracefully stop the scheduler on interpreter exit."""
    try:
        scheduler.shutdown(wait=False)
    except Exception:  # pragma: no cover
        pass
