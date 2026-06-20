"""
Smart categorisation of incoming articles.

Strategy (hybrid, as agreed in the plan):
  1. Build a keyword index from every ``Category.keywords`` field.
  2. Score each category by how many of its keywords appear in the article's
     title + summary. The category with the highest hit count wins.
  3. If no keyword matches at all, fall back to the feed's ``default_category``
     (or None for manual articles).

This is intentionally lightweight: no ML, no external API, fully offline, and
easy to tune simply by editing keywords in the admin.
"""

import logging
from typing import Optional

from django.core.cache import cache

logger = logging.getLogger(__name__)

# Cache the keyword index for a few minutes so we don't re-read the Category
# table for every single feed item.
_INDEX_CACHE_KEY = 'news:category_keyword_index'
_INDEX_CACHE_TTL = 5 * 60  # seconds


def build_keyword_index():
    """
    Build a list of ``(category_id, [keywords])`` tuples.

    Uses ``cache`` so repeated calls during a single fetch run are cheap. The
    cache is invalidated whenever a category is saved (see the signal below).
    """
    from apps.news.models import Category

    cached = cache.get(_INDEX_CACHE_KEY)
    if cached is not None:
        return cached

    index = [(cat.id, cat.keyword_list()) for cat in Category.objects.all()]
    cache.set(_INDEX_CACHE_KEY, index, _INDEX_CACHE_TTL)
    return index


def invalidate_keyword_index(**kwargs):
    """Signal receiver: drop the cached keyword index so it is rebuilt."""
    cache.delete(_INDEX_CACHE_KEY)


def _score_text(text: str, keywords) -> int:
    """Count how many of ``keywords`` appear in ``text`` (case-insensitive)."""
    if not text or not keywords:
        return 0
    lowered = text.lower()
    return sum(1 for kw in keywords if kw and kw in lowered)


def categorize(title: str, summary: str = '', fallback_category=None) -> Optional[object]:
    """
    Pick the best ``Category`` instance for the given text.

    Args:
        title:    Article title (required, always considered).
        summary:  Article summary/excerpt (optional, helps disambiguation).
        fallback_category: returned when nothing matched (e.g. the feed's
                           default category). May be a Category instance or None.

    Returns:
        A ``Category`` instance, or ``fallback_category`` (possibly None) when
        no keyword matched.
    """
    from apps.news.models import Category

    haystack = ' '.join(part for part in (title, summary) if part)

    best_id = None
    best_score = 0
    for cat_id, keywords in build_keyword_index():
        if not keywords:
            continue
        score = _score_text(haystack, keywords)
        if score > best_score:
            best_score = score
            best_id = cat_id

    if best_id is not None:
        return Category.objects.filter(pk=best_id).first()
    return fallback_category


# Invalidate the cached index whenever a Category changes.
from django.db.models.signals import post_save, post_delete  # noqa: E402
# Local import of the Category model is deferred to inside build_keyword_index
# to avoid an import cycle at module load time, but we still need a reference
# to the sender for the signal. We connect lazily via a small app-ready hook
# in apps.news.apps to avoid touching models at import time here.
