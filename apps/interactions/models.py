"""
Database models for the `interactions` app: comments and likes/dislikes.

Both models target anonymous visitors (no user registration required):
  * ``Comment``  – moderated. New comments default to ``is_approved = False``
                   and become visible only after an admin approves them.
  * ``Like``     – one vote per browser session (identified by a random token
                   stored in the session, see ``settings.LIKE_SESSION_KEY``).
                   Counters on the article (likes_count / dislikes_count) are
                   updated by signals so list views stay cheap.
"""

from django.conf import settings
from django.db import models


# ---------------------------------------------------------------------------
# Comment
# ---------------------------------------------------------------------------
class Comment(models.Model):
    """A moderated reader comment attached to an article."""

    article = models.ForeignKey(
        'news.Article',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='خبر',
    )
    name = models.CharField('نام', max_length=80)
    email = models.EmailField('ایمیل', blank=True)
    body = models.TextField('متن نظر', max_length=2000)

    # Moderation: comments are hidden until approved by an admin.
    is_approved = models.BooleanField('تأیید شده', default=False)

    created_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)

    class Meta:
        verbose_name = 'نظر'
        verbose_name_plural = 'نظرات'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['article', 'is_approved', '-created_at'])]

    def __str__(self) -> str:
        return f'{self.name} — {self.article.title[:40]}'


# ---------------------------------------------------------------------------
# Like / Dislike
# ---------------------------------------------------------------------------
class Like(models.Model):
    """
    An anonymous vote (+1 like / -1 dislike) for an article.

    A per-browser token (saved in the Django session) identifies the voter so
    we can enforce "one vote per visitor per article" and let them switch
    between like and dislike.
    """

    LIKE = 1
    DISLIKE = -1
    VALUE_CHOICES = (
        (LIKE, 'لایک'),
        (DISLIKE, 'دیسلایک'),
    )

    article = models.ForeignKey(
        'news.Article',
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='خبر',
    )
    token = models.CharField('شناسه رای‌دهنده', max_length=64, db_index=True)
    value = models.SmallIntegerField('نوع رای', choices=VALUE_CHOICES)

    created_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)
    updated_at = models.DateTimeField('تاریخ به‌روزرسانی', auto_now=True)

    class Meta:
        verbose_name = 'رای'
        verbose_name_plural = 'آرا'
        # A token can have exactly one (latest) vote per article.
        unique_together = ('article', 'token')
        indexes = [models.Index(fields=['article', 'token'])]

    def __str__(self) -> str:
        return f'{self.get_value_display()} روی {self.article.title[:40]}'
    
    
# ---------------------------------------------------------------------------
# Signals: keep article counters in sync with votes.
# ---------------------------------------------------------------------------
from django.db.models.signals import post_save, post_delete  # noqa: E402
from django.dispatch import receiver  # noqa: E402


def _recount(article):
    """Recompute likes_count / dislikes_count from the Like rows (robust)."""
    if article is None:
        return
    likes = article.likes.filter(value=Like.LIKE).count()
    dislikes = article.likes.filter(value=Like.DISLIKE).count()
    # update() avoids triggering save() recursively and is a single query.
    type(article).objects.filter(pk=article.pk).update(
        likes_count=likes, dislikes_count=dislikes,
    )


@receiver(post_save, sender=Like)
def _on_like_save(sender, instance, **kwargs):
    _recount(instance.article)


@receiver(post_delete, sender=Like)
def _on_like_delete(sender, instance, **kwargs):
    _recount(instance.article)
