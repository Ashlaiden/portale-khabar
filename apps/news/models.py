"""
Database models for the `news` app.

There are three core models:

  * ``Category``  – a topic (سیاسی، اقتصادی، …) with Persian keywords used by
                    the smart categoriser to auto-classify incoming RSS items.
  * ``Article``   – the actual news story. Can be created by hand in the admin
                    or imported from an RSS feed. Imported articles keep their
                    source name (خبرگزاری) so it can be shown next to the story.
  * ``RSSFeed``   – a managed feed source with its own fetch interval. The
                    background scheduler iterates over active feeds and pulls
                    new articles into ``Article``.

Design notes:
  * Both a local ``image`` (manual upload) and an ``image_url`` (for RSS)
    exist on Article. Only one is used at a time, which keeps storage cheap
    while still supporting hand-picked imagery for editorial content.
  * ``dedup_hash`` is a normalised+hashed form of the title used by the
    duplicate filter (see ``services/dedup.py``) so we never import the same
    story twice, even when the title is slightly reworded.
"""

import hashlib

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.db.models.signals import pre_save


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------
class Category(models.Model):
    """
    A topic category (e.g. سیاسی، اقتصادی، ورزشی، فناوری).

    The ``keywords`` field holds a comma-separated list of Persian terms. The
    smart categoriser scans an article's title + summary for these keywords to
    pick the best category automatically.
    """

    name = models.CharField('نام', max_length=80, unique=True)
    slug = models.SlugField('نامک', max_length=100, unique=True, blank=True)
    # Comma-separated Persian keywords used by the categoriser.
    keywords = models.TextField(
        'کلمات کلیدی برای دسته‌بندی خودکار',
        blank=True,
        help_text='کلمات کلیدی فارسی را با کاما جدا کنید. مثال: فوتبال، والیبال',
    )
    # Optional Tailwind colour token used for the category badge in templates.
    color = models.CharField('رنگ نشان', max_length=40, default='bg-indigo-500/20 text-indigo-300')
    # Manual ordering in the admin / menus.
    order = models.PositiveIntegerField('ترتیب نمایش', default=0)

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'
        ordering = ['order', 'name']

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        # Auto-fill the slug from the name if the admin left it empty.
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def keyword_list(self):
        """Return keywords as a cleaned Python list (lower-cased, stripped)."""
        return [k.strip().lower() for k in self.keywords.split(',') if k.strip()]


# ---------------------------------------------------------------------------
# Article
# ---------------------------------------------------------------------------
class Article(models.Model):
    """
    A news article.

    Articles come from two channels:
      1. Manual entry by an editor (``is_rss = False``). A local image can be
         uploaded.
      2. Automatic import from an RSS feed (``is_rss = True``). The original
         image URL is stored (no download) and ``source_name`` records the
         agency (خبرگزاری) so it can be credited next to the story.
    """

    title = models.CharField('عنوان', max_length=300)
    slug = models.SlugField('نامک', max_length=350, unique=True, blank=True)
    summary = models.TextField('خلاصه', blank=True)
    content = models.TextField('متن خبر', blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        verbose_name='دسته‌بندی',
    )

    # Manual upload (editors). Stored under MEDIA_ROOT.
    image = models.ImageField('تصویر آپلودی', upload_to='articles/%Y/%m/', blank=True, null=True)
    # Remote image URL for RSS-sourced articles (stored, not downloaded).
    image_url = models.URLField('آدرس تصویر (RSS)', blank=True, null=True)

    # Publishing / visibility -------------------------------------------------
    is_published = models.BooleanField('منتشر شده', default=True)
    is_featured = models.BooleanField('خبر ویژه (صفحه خانه)', default=False)
    is_rss = models.BooleanField('خبر RSS', default=False)
    published_at = models.DateTimeField('تاریخ انتشار', default=timezone.now)
    created_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)
    updated_at = models.DateTimeField('تاریخ به‌روزرسانی', auto_now=True)

    # RSS provenance ----------------------------------------------------------
    feed = models.ForeignKey(
        'RSSFeed',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        verbose_name='منبع RSS',
    )
    source_name = models.CharField('نام خبرگزاری', max_length=150, blank=True)
    source_url = models.URLField('لینک منبع', blank=True)

    # Duplicate detection -----------------------------------------------------
    # Normalised+hashed title; see services/dedup.py for the normaliser.
    dedup_hash = models.CharField(
        'هش یکتایی (ضد تکرار)', max_length=64, db_index=True, blank=True, default='',
    )

    # Light-weight counters kept on the article for fast sorting in lists.
    likes_count = models.PositiveIntegerField('لایک', default=0)
    dislikes_count = models.PositiveIntegerField('دیسلایک', default=0)
    views_count = models.PositiveIntegerField('بازدید', default=0)

    class Meta:
        verbose_name = 'خبر'
        verbose_name_plural = 'اخبار'
        ordering = ['-published_at', '-id']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['is_published', 'is_featured']),
            models.Index(fields=['dedup_hash']),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        # Auto-fill slug from title.
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or 'article'
            self.slug = base
            n = 1
            qs = Article.objects.filter(slug__startswith=self.slug).exclude(pk=self.pk)
            while qs.filter(slug=self.slug).exists():
                n += 1
                self.slug = f'{base}-{n}'

        # Automatic categorization only for articles without a pre-assigned category.
        if not self.category_id:
            # Priority 1: If the feed has a default category, use it and bypass the algorithm.
            if self.feed_id and self.feed and self.feed.default_category:
                self.category = self.feed.default_category
            else:
                # Priority 2: Smart keyword-based hybrid categorization.
                from apps.news.services import categorizer
                cat = categorizer(self.title, self.summary or '')
                if cat:
                    self.category = cat

        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse('news:detail', kwargs={'slug': self.slug})

    # -- Image helpers --------------------------------------------------------
    def get_image_url(self):
        """Return whichever image source is available (local upload > RSS URL)."""
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return ''

    @property
    def has_image(self) -> bool:
        return bool(self.image or self.image_url)

    @property
    def net_score(self) -> int:
        """likes - dislikes, handy for "popular" sorts."""
        return self.likes_count - self.dislikes_count


# ---------------------------------------------------------------------------
# RSS Feed
# ---------------------------------------------------------------------------
class RSSFeed(models.Model):
    """
    A managed RSS/Atom feed source.

    Each feed carries its own ``fetch_interval_minutes`` so a fast agency can
    be polled more often than a weekly digest feed. The scheduler only visits
    feeds whose ``is_active`` flag is set and whose interval has elapsed.
    """

    name = models.CharField('دسته خبری', max_length=150, unique=True)
    title = models.CharField('نام خبرگزاری', max_length=150, unique=False)
    url = models.URLField('آدرس RSS', unique=True)
    website = models.URLField('وب‌سایت', blank=True, help_text='اختیاری؛ برای نمایش در منبع خبر')
    default_category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feeds',
        verbose_name='دسته پیش‌فرض',
        help_text='اگر دسته‌بندی هوشمند نتواند دسته‌ای پیدا کند، از این استفاده می‌شود.',
    )
    is_active = models.BooleanField('فعال', default=True)
    fetch_interval_minutes = models.PositiveIntegerField(
        'بازه دریافت (دقیقه)', default=30,
        help_text='هر چند دقیقه یک‌بار این فید بررسی شود.',
    )
    last_fetched_at = models.DateTimeField('آخرین دریافت', null=True, blank=True)
    # Track problems so the admin can flag broken feeds.
    last_error = models.TextField('آخرین خطا', blank=True, default='')
    created_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)

    class Meta:
        verbose_name = 'منبع RSS'
        verbose_name_plural = 'منابع RSS'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

    @property
    def is_due(self) -> bool:
        """True if this feed should be fetched again according to its interval."""
        if not self.is_active:
            return False
        if not self.last_fetched_at:
            return True
        from datetime import timedelta
        return timezone.now() >= self.last_fetched_at + timedelta(minutes=self.fetch_interval_minutes)

    @staticmethod
    def make_dedup_hash(title: str) -> str:
        """Tiny convenience wrapper used by importers/tests."""
        from apps.news.services import dedup
        return dedup.title_hash(title)


# ---------------------------------------------------------------------------
# Helper: compute dedup_hash at the model layer for manual entries too.
# ---------------------------------------------------------------------------
def _article_pre_save(sender, instance, **kwargs):
    """Ensure every article has a dedup_hash before hitting the DB."""
    if not instance.dedup_hash and instance.title:
        from apps.news.services import dedup
        instance.dedup_hash = dedup.title_hash(instance.title)

# Wire up the signal at import time so it is active everywhere the app loads.
pre_save.connect(_article_pre_save, sender=Article)
