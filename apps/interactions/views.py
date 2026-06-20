"""
Views for reader interactions: posting comments and voting (like/dislike).

Both endpoints work for anonymous visitors (no user account). Comments are
always moderated (``is_approved = False`` on creation); votes are tracked with
a per-browser session token (see ``apps.news.views._get_like_token``).

``toggle_like`` returns JSON so it can be called from JavaScript; the matching
client code lives in ``static/js/main.js``.
"""

import uuid

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from apps.news.models import Article

from .models import Comment, Like


# ---------------------------------------------------------------------------
# Comment submission
# ---------------------------------------------------------------------------
@csrf_protect
@require_POST
def add_comment(request, article_id):
    """
    Submit a new comment on an article.

    The comment is created with ``is_approved=False`` so it stays hidden until
    an admin approves it. Works both via AJAX (returns JSON) and as a normal
    form POST (redirects back to the article).
    """
    article = get_object_or_404(Article, pk=article_id, is_published=True)

    name = (request.POST.get('name') or '').strip()
    email = (request.POST.get('email') or '').strip()
    body = (request.POST.get('body') or '').strip()

    # Basic server-side validation. Keep it light; admin moderation handles
    # the rest.
    if not name or not body:
        msg = 'نام و متن نظر الزامی هستند.'
        if _wants_json(request):
            return JsonResponse({'ok': False, 'error': msg}, status=400)
        messages.error(request, msg)
        return redirect(article.get_absolute_url())

    if len(body) > 2000:
        msg = 'متن نظر بیش از حد طولانی است.'
        if _wants_json(request):
            return JsonResponse({'ok': False, 'error': msg}, status=400)
        messages.error(request, msg)
        return redirect(article.get_absolute_url())

    Comment.objects.create(article=article, name=name, email=email, body=body)

    success_msg = 'نظر شما ثبت شد و پس از تأیید مدیر نمایش داده می‌شود.'
    if _wants_json(request):
        return JsonResponse({'ok': True, 'message': success_msg})
    messages.success(request, success_msg)
    return redirect(article.get_absolute_url())


# ---------------------------------------------------------------------------
# Like / Dislike toggle
# ---------------------------------------------------------------------------
@csrf_protect
@require_POST
def toggle_like(request, article_id):
    """
    Set, switch or remove the visitor's vote on an article.

    Request body / form fields:
        value:  'like' | 'dislike'   (set or switch the vote)
        value:  '0'                  (retract the current vote)

    Returns JSON:
        {ok: true, value: -1|0|1, likes: N, dislikes: M}
    """
    article = get_object_or_404(Article, pk=article_id, is_published=True)

    raw_value = (request.POST.get('value') or '').strip().lower()
    if raw_value == 'like':
        new_value = Like.LIKE
    elif raw_value == 'dislike':
        new_value = Like.DISLIKE
    else:
        # Anything else (incl. '0') means "remove my vote".
        new_value = None

    token = _ensure_token(request)

    # Fetch the visitor's existing vote on this article, if any.
    existing = Like.objects.filter(article=article, token=token).first()

    if new_value is None:
        # Retract the vote.
        if existing:
            existing.delete()
    elif existing is None:
        # First vote on this article.
        Like.objects.create(article=article, token=token, value=new_value)
    elif existing.value != new_value:
        # Switch between like and dislike.
        existing.value = new_value
        existing.save(update_fields=['value', 'updated_at'])
    # else: same vote again -> no-op.

    # Refresh counters from the DB (signals keep them in sync).
    article.refresh_from_db()

    return JsonResponse({
        'ok': True,
        'value': new_value if new_value is not None else 0,
        'likes': article.likes_count,
        'dislikes': article.dislikes_count,
    })


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _wants_json(request) -> bool:
    """True if the client explicitly asked for JSON (AJAX / Accept header)."""
    accept = request.META.get('HTTP_ACCEPT', '')
    xhr = request.headers.get('X-Requested-With', '')
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in accept or xhr.lower() == 'xmlhttprequest'


def _ensure_token(request) -> str:
    """
    Return (and lazily create) the per-browser voting token stored in session.
    """
    if not request.session.session_key:
        request.session.save()
    token = request.session.get(settings.LIKE_SESSION_KEY)
    if not token:
        token = uuid.uuid4().hex
        request.session[settings.LIKE_SESSION_KEY] = token
        request.session.modified = True
    return token
