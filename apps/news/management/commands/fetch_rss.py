"""
``python manage.py fetch_rss`` – manually pull RSS feeds.

This is handy for testing the importer without waiting for the scheduler, and
for running feeds on a schedule via a system cron / Task Scheduler if you
prefer that over the in-process scheduler.

Usage:
    python manage.py fetch_rss               # all active feeds (even if not due)
    python manage.py fetch_rss --feed-id 3   # only the given feed
    python manage.py fetch_rss --due-only    # respect each feed's interval
"""

from django.core.management.base import BaseCommand

from apps.news.models import RSSFeed
from apps.news.services import rss_fetcher


class Command(BaseCommand):
    help = 'Download and import articles from RSS feeds.'

    def add_arguments(self, parser):
        # Optionally restrict to a single feed by primary key.
        parser.add_argument(
            '--feed-id',
            type=int,
            default=None,
            help='Only fetch the feed with this primary key.',
        )
        # Optionally respect each feed's individual interval.
        parser.add_argument(
            '--due-only',
            action='store_true',
            default=False,
            help='Skip feeds whose fetch interval has not yet elapsed.',
        )

    def handle(self, *args, **options):
        feed_id = options['feed_id']
        due_only = options['due_only']

        if feed_id is not None:
            # Specific feed: error out if it doesn't exist.
            try:
                feeds = [RSSFeed.objects.get(pk=feed_id)]
            except RSSFeed.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'No feed with id={feed_id}.'))
                return
        else:
            feeds = list(RSSFeed.objects.filter(is_active=True))

        total_created = 0
        total_skipped = 0
        for feed in feeds:
            if due_only and not feed.is_due:
                self.stdout.write(f'  skip (not due): {feed.name}')
                continue
            created, skipped = rss_fetcher.fetch_feed(feed)
            total_created += created
            total_skipped += skipped
            self.stdout.write(
                self.style.SUCCESS(
                    f'  {feed.name}: +{created} new, {skipped} skipped'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. Total: +{total_created} new, {total_skipped} skipped.'
            )
        )
