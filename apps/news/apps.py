"""
App configuration for the `news` app.

This is the core content app: it owns Categories, Articles and RSS feeds,
plus the background scheduler that periodically pulls new articles from the
configured RSS sources. The scheduler is started from ``ready()`` so it spins
up automatically together with the Django process (dev server or WSGI/ASGI).
"""

import logging
import os

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.news'
    # Human-readable label shown in the admin.
    verbose_name = 'اخبار'

    def ready(self):
        """
        Called once Django is fully loaded. We do two things here:

          1. Connect cross-module signals (e.g. invalidate the categoriser's
             cached keyword index when a category changes).
          2. Optionally start the background RSS scheduler.

        Both are wrapped defensively so a failure in one doesn't break app
        loading.
        """
        # 1) Signals must always be connected (needed by admin & imports too).
        try:
            self._connect_signals()
        except Exception:  # pragma: no cover
            logger.exception('Failed to connect news app signals.')

        # 2) Scheduler only runs under the real server, never during
        # management commands such as `migrate` or `collectstatic`.
        # The dev server autoreloader spawns a child whose RUN_MAIN env var
        # is set to 'true'; we schedule inside that child only, to avoid
        # running jobs twice. Standalone servers (gunicorn/uwsgi) should set
        # ENABLE_SCHEDULER explicitly.
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('ENABLE_SCHEDULER'):
            try:
                from . import scheduler  # noqa: F401  (import has side effects)
                scheduler.start()
            except Exception:  # pragma: no cover - never crash the app
                logger.exception('Failed to start the RSS scheduler; it will not run.')

    def _connect_signals(self):
        """
        Hook up cross-module signals that need the app registry to be ready.

        We do this from ``ready()`` (rather than at import time inside the
        service module) because connecting to ``Category`` requires the model
        to be importable, which is only true once apps are loaded.
        """
        from django.db.models.signals import post_save, post_delete

        from .models import Category
        from .services import categorizer

        # Invalidate the cached keyword index whenever a category changes so
        # newly-added keywords take effect immediately.
        post_save.connect(categorizer.invalidate_keyword_index, sender=Category)
        post_delete.connect(categorizer.invalidate_keyword_index, sender=Category)
