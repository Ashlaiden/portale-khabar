"""
Views for the public news site.

The views here are deliberately thin: filtering logic lives in the queryset
helpers on the models / a small ``queries`` module so it can be reused. Each
view only prepares context and picks a template.

Filters supported on the news list:
  * ``category``  – slug of a Category.
  * ``date``      – one of: today, week, month  (relative publication date).
  * ``q``         – free-text search over title + summary.
"""

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from django.core.cache import cache
from .models import Article, Category
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

# ---------------------------------------------------------------------------
# Small queryset helpers (kept here for readability; not large enough to need
# a separate queries module yet).
# ---------------------------------------------------------------------------
def _published(qs):
    """Only published articles, ordered by newest first."""
    return qs.filter(is_published=True).order_by('-published_at', '-id')


def _latest(qs, count):
    """Return the most recent N published articles (for sidebars/widgets)."""
    return list(_published(qs)[:count])


def _apply_filters(qs, request):
    """
    Apply the optional list filters (category / date / search) to ``qs``.

    Returns the filtered queryset. Safe to call when no filters are set —
    the queryset is returned unchanged.
    """
    # Category filter.
    category_slug = request.GET.get('category')
    if category_slug:
        qs = qs.filter(category__slug=category_slug)

    # Date filter (relative ranges in the site's timezone).
    date_filter = request.GET.get('date')
    if date_filter in ('today', 'week', 'month'):
        from datetime import timedelta
        from django.utils import timezone
        ranges = {
            'today': timedelta(hours=24),
            'week': timedelta(days=7),
            'month': timedelta(days=30),
        }
        since = timezone.now() - ranges[date_filter]
        qs = qs.filter(published_at__gte=since)

    # Full-text-ish search across title + summary + content.
    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(summary__icontains=q)
            | Q(content__icontains=q)
        )
    return qs


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------
@require_GET
def home(request):
    """
    Home page.

    Shows a row of large featured boxes (or the newest articles if nothing is
    marked featured), a grid of the latest news, and the shared sidebar.
    """
    featured_count = getattr(settings, 'NEWS_FEATURED_COUNT', 3)
    sidebar_count = getattr(settings, 'NEWS_SIDEBAR_COUNT', 8)

    # Featured big boxes (fallback: newest articles if none flagged).
    featured = list(
        _published(Article.objects).filter(is_featured=True)[:featured_count]
    )
    if len(featured) < featured_count:
        extra = _latest(Article.objects.exclude(pk__in=[a.pk for a in featured]),
                        featured_count - len(featured))
        featured.extend(extra)

    # Regular latest news grid (exclude the ones already shown as featured).
    featured_ids = [a.pk for a in featured]
    latest = _latest(Article.objects.exclude(pk__in=featured_ids), 9)

    # Sidebar: newest items regardless of featured state.
    sidebar_news = _latest(Article.objects, sidebar_count)

    context = {
        'featured_news': featured,
        'latest_news': latest,
        'sidebar_news': sidebar_news,
        'active_menu': 'home',
    }
    return render(request, 'pages/home.html', context)


@require_GET
def news_list(request, slug=None):
    """
    News listing with filters (category / date / search) and pagination.

    ``slug`` is optional and used by the ``news:category`` route to pre-filter
    the list to a single category.
    """
    from django.core.paginator import Paginator

    page_size = getattr(settings, 'NEWS_PAGE_SIZE', 9)
    sidebar_count = getattr(settings, 'NEWS_SIDEBAR_COUNT', 8)

    qs = _apply_filters(_published(Article.objects), request)
    # If accessed via /news/category/<slug>/, restrict to that category and
    # also reflect it in the active filter state for the UI.
    if slug:
        qs = qs.filter(category__slug=slug)

    paginator = Paginator(qs, page_size)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'sidebar_news': _latest(Article.objects, sidebar_count),
        # Echo current filters back into the template for the active states.
        'active_category': slug or request.GET.get('category', ''),
        'active_date': request.GET.get('date', ''),
        'active_query': request.GET.get('q', ''),
        'active_menu': 'news',
        'page_title': 'همه اخبار',
    }
    return render(request, 'pages/news_list.html', context)


@require_GET
def rss_news_list(request):
    """News listing filtered to RSS-sourced articles only."""
    from django.core.paginator import Paginator

    page_size = getattr(settings, 'NEWS_PAGE_SIZE', 9)
    sidebar_count = getattr(settings, 'NEWS_SIDEBAR_COUNT', 8)

    qs = _apply_filters(_published(Article.objects.filter(is_rss=True)), request)
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'page_obj': page_obj,
        'sidebar_news': _latest(Article.objects, sidebar_count),
        'active_category': request.GET.get('category', ''),
        'active_date': request.GET.get('date', ''),
        'active_query': request.GET.get('q', ''),
        'active_menu': 'rss',
        'page_title': 'اخبار RSS',
    }
    return render(request, 'pages/news_list.html', context)


@require_GET
def search(request):
    """Shortcut view for the navbar search box. Reuses the list template."""
    return news_list(request)


def news_detail(request, slug):
    """
    Single article page.

    Shows the article body, the comment list (approved only), the comment
    form and the like/dislike widget. GET (not require_GET) so that comment
    POSTs redirected back here still render fine.
    """
    from apps.interactions.models import Comment, Like

    sidebar_count = getattr(settings, 'NEWS_SIDEBAR_COUNT', 8)

    article = get_object_or_404(Article, slug=slug, is_published=True)

    # Increment view counter cheaply (no save() => no signals/recursion).
    Article.objects.filter(pk=article.pk).update(views_count=article.views_count + 1)
    article.views_count += 1  # keep local copy in sync for the template

    # Approved comments, newest first.
    comments = article.comments.filter(is_approved=True).order_by('-created_at')

    # Has this browser already voted? Used to highlight the active button.
    token = _get_like_token(request)
    user_vote = Like.objects.filter(article=article, token=token).first()

    # Related articles in the same category (excluding current).
    related = list(
        _published(Article.objects.filter(category=article.category).exclude(pk=article.pk))[:4]
    )

    context = {
        'article': article,
        'comments': comments,
        'comments_count': comments.count(),
        'user_vote': user_vote.value if user_vote else 0,
        'related_news': related,
        'sidebar_news': _latest(Article.objects.exclude(pk=article.pk), sidebar_count),
        'active_menu': 'news',
    }
    return render(request, 'pages/news_detail.html', context)

@csrf_protect
@require_POST
def refresh_static(request):
    from django.core.cache import cache
    cache.set('static_version', (cache.get('static_version') or 1) + 1)
    return JsonResponse({'ok': True})

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_like_token(request):
    """
    Return the per-browser voting token, creating one if needed.

    The token is stored in the session so we can enforce "one vote per visitor
    per article" without requiring a user account.
    """
    if not request.session.session_key:
        request.session.save()
    token = request.session.get(settings.LIKE_SESSION_KEY)
    if not token:
        import uuid
        token = uuid.uuid4().hex
        request.session[settings.LIKE_SESSION_KEY] = token
        request.session.modified = True
    return token
