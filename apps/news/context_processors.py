"""
Template context processors for the news app.

A context processor runs on *every* template render, so these must stay cheap.
We expose a small set of site-wide values that many templates need (nav menu,
categories, …) so individual views don't have to repeat themselves.
"""

from django.conf import settings

from .models import Category


def site_context(request):
    """
    Inject values used across the whole site (header/footer/sidebars).

    Exposed keys:
      * ``SITE_NAME``        – brand name shown in the navbar/footer.
      * ``SITE_CATEGORIES``  – ordered list of categories for the navbar menu.
      * ``NEWS_SIDEBAR_COUNT`` – how many items the latest-news sidebar shows.
    """
    # Cheap query: a handful of category rows. Cached results from the ORM
    # would be an option if the count ever grows large.
    categories = list(Category.objects.all().order_by('order', 'name'))

    return {
        'SITE_NAME': 'پرتال خبری',
        'SITE_CATEGORIES': categories,
        'NEWS_SIDEBAR_COUNT': getattr(settings, 'NEWS_SIDEBAR_COUNT', 8),
    }
