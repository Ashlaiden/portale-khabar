"""
RSS feed fetching & importing.

Entry points:
  * ``fetch_feed(feed)``        – pull one feed, creating Article rows for every
                                  new item. Returns ``(created, skipped)``.
  * ``fetch_all_due_feeds()``   – iterate every active feed whose interval has
                                  elapsed. Used by the scheduler and the
                                  ``fetch_rss`` management command.

The module relies on:
  * ``feedparser`` to download/parse the feed,
  * ``python-dateutil`` to parse the variety of date formats feeds publish,
  * ``services.dedup`` to skip items we already imported,
  * ``services.categorizer`` to pick the best category for each item.

Robustness:
  * Network errors are caught per-feed and recorded on ``feed.last_error``
    so the admin surface shows broken feeds.
  * Items without a usable title are skipped silently.
"""

import logging
import ssl
from datetime import datetime, timezone as dt_tz
import requests
import feedparser
from dateutil import parser as date_parser
from django.utils import timezone
from . import categorizer, dedup
import urllib.request

logger = logging.getLogger(__name__)

# Cap how many entries per feed we will consider in a single pass. Most feeds
# list 20–50 items; older items are unlikely to be "news" anymore.
MAX_ENTRIES_PER_FEED = 60

# User-Agent: some agencies block the default feedparser UA, so we send one
# that looks like a normal reader.
USER_AGENT = 'PortaleKhabar/1.0 (+news aggregator; RSS reader)'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _parse_date(entry) -> datetime:
    """
    Best-effort parse of an entry's published/updated date.

    Returns a timezone-aware datetime (UTC) or ``timezone.now()`` as a last
    resort, so the article always has a sensible ``published_at``.
    """
    raw = entry.get('published') or entry.get('updated') or entry.get('created')
    if not raw:
        return timezone.now()
    try:
        dt = date_parser.parse(raw)
    except (ValueError, TypeError, OverflowError):
        return timezone.now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=dt_tz.utc)
    return dt


def _get_image_url(entry) -> str:
    """
    Try a few common places to find an image URL for a feed entry.

    RSS has no single standard for images, so we check the most popular
    extensions (media:content, enclosures, media:thumbnail, image field).
    """
    # media:content / media:thumbnail (media RSS).
    for key in ('media_content', 'media_thumbnail'):
        items = entry.get(key) or []
        for it in items:
            url = it.get('url')
            if url:
                return url
    # <enclosure url="..." type="image/...">
    for enc in entry.get('enclosures', []) or []:
        url = enc.get('href') or enc.get('url')
        if url and ('image' in (enc.get('type') or '') or url):
            return url
    # Some feeds put a plain 'image' field.
    img = entry.get('image')
    if isinstance(img, dict) and img.get('url'):
        return img['url']
    if isinstance(img, str) and img.startswith('http'):
        return img
    return ''


def _strip_html(text) -> str:
    """Remove HTML tags and decode entities from a string."""
    if not text:
        return ''
    import re
    # Remove HTML tags.
    clean = re.sub(r'<[^>]+>', '', str(text))
    # Collapse whitespace.
    return ' '.join(clean.split())


# ---------------------------------------------------------------------------
# Core fetch logic
# ---------------------------------------------------------------------------
requests.packages.urllib3.disable_warnings()
_session = requests.Session()
_session.headers.update({'User-Agent': USER_AGENT})
def fetch_feed(feed) -> tuple:
    """
    Download and import one feed.

    Returns ``(created_count, skipped_count)``. The feed's ``last_fetched_at``
    and ``last_error`` are always updated.
    """
    # Import here to avoid a circular import at module load time.
    from apps.news.models import Article

    created = 0
    skipped = 0
    feed.last_fetched_at = timezone.now()

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1
    ssl_ctx.set_ciphers('DEFAULT:@SECLEVEL=0')
    handler = urllib.request.HTTPSHandler(context=ssl_ctx)

    xml_data = None
    for url in (feed.url, feed.url.replace('https://', 'http://')):
        try:
            resp = _session.get(url, verify=False, timeout=15)
            resp.raise_for_status()
            xml_data = resp.content
            break
        except Exception:
            continue

    if not xml_data:
        feed.last_error = f'fetch error: could not connect to {feed.url}'[:500]
        feed.save(update_fields=['last_fetched_at', 'last_error'])
        logger.warning('Failed to fetch feed %s', feed.name)
        return 0, 0

    parsed = feedparser.parse(xml_data)

    # try:
    #     response = requests.get(feed.url, headers={'User-Agent': USER_AGENT}, verify=False, timeout=15)
    #     parsed = feedparser.parse(response.content)
    # except Exception as exc:  # network / parsing error
    #     feed.last_error = f'fetch error: {exc!s}'[:500]
    #     feed.save(update_fields=['last_fetched_at', 'last_error'])
    #     logger.exception('Failed to fetch feed %s', feed.name)
    #     return 0, 0

    # feedparser records problems in bozo; log but keep going if we have entries.
    if parsed.bozo and not getattr(parsed, 'entries', None):
        feed.last_error = f'parse error: {parsed.bozo_exception!s}'[:500]
        feed.save(update_fields=['last_fetched_at', 'last_error'])
        logger.warning('Feed %s returned a parse error: %s', feed.name, parsed.bozo_exception)
        return 0, 0

    entries = list(getattr(parsed, 'entries', []) or [])[:MAX_ENTRIES_PER_FEED]
    for entry in entries:
        title = _strip_html(entry.get('title'))
        if not title:
            skipped += 1
            continue

        # Duplicate detection: skip if we have already imported this title.
        h = dedup.title_hash(title)
        if Article.objects.filter(dedup_hash=h).exists():
            skipped += 1
            continue
        # Also check by source URL — more reliable than title hashing.
        if link and Article.objects.filter(source_url=link).exists():
            skipped += 1
            continue

        summary = _strip_html(entry.get('summary') or entry.get('description'))
        link = entry.get('link') or ''
        image_url = _get_image_url(entry)
        published_at = _parse_date(entry)

        # Categorisation strategy:
        #   If the feed has a default category, use it directly (no smart scoring).
        #   Otherwise, leave category as None — the pre_save signal on Article
        #   will auto-categorize via keyword matching.
        category = feed.default_category if feed.default_category_id else None

        Article.objects.create(
            title=title,
            summary=summary,
            content='',  # RSS items usually only carry a summary.
            category=category,
            image_url=image_url,
            is_rss=True,
            published_at=published_at,
            feed=feed,
            source_name=feed.title,
            source_url=link,
            dedup_hash=h,
        )
        created += 1

    feed.last_error = ''
    feed.save(update_fields=['last_fetched_at', 'last_error'])
    logger.info('Feed %s: imported %d, skipped %d', feed.name, created, skipped)

    # Tidy up: prune very old items so the DB stays small.
    _prune_feed(feed)

    return created, skipped


def fetch_all_due_feeds() -> dict:
    """
    Fetch every active feed whose fetch interval has elapsed.

    Returns a dict ``{feed_name: (created, skipped)}`` for logging / display.
    """
    from apps.news.models import RSSFeed

    results = {}
    for feed in RSSFeed.objects.filter(is_active=True):
        if not feed.is_due:
            continue
        try:
            results[feed.name] = fetch_feed(feed)
        except Exception:  # pragma: no cover - defensive: never crash the loop
            logger.exception('Unhandled error while fetching feed %s', feed.name)
            results[feed.name] = (0, 0)
    return results


def _prune_feed(feed):
    """
    Keep only the most recent ``RSS_MAX_ITEMS_PER_FEED`` items for a feed.

    Older articles are deleted to keep the SQLite DB compact. Set the cap to 0
    in settings to disable pruning entirely.
    """
    from django.conf import settings as dj_settings
    from apps.news.models import Article

    cap = getattr(dj_settings, 'RSS_MAX_ITEMS_PER_FEED', 0) or 0
    if cap <= 0:
        return

    # Find the id at the cutoff (N newest) and delete everything older.
    cutoff = (
        Article.objects.filter(feed=feed)
        .order_by('-published_at', '-id')
        .values_list('pk', flat=True)[cap:cap + 1]
    )
    if cutoff:
        Article.objects.filter(feed=feed, pk__in=list(
            Article.objects.filter(feed=feed, pk__lt=cutoff[0]).values_list('pk', flat=True)
        )).delete()
