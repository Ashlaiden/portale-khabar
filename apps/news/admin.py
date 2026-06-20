"""
Admin configuration for the news app (with django-jazzmin tweaks).

Each ModelAdmin is tuned for editors:
  * Search/filter/list display so common tasks are one click away.
  * Custom ``fetch_now`` action on RSSFeed to refresh a feed on demand.
  * Tabular inline of categories on Article is intentionally omitted to keep
    the change form simple.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Article, Category, RSSFeed
from .services import rss_fetcher


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'articles_count', 'keywords_preview')
    list_editable = ('order',)
    search_fields = ('name', 'keywords')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')

    # -- list_display helpers ------------------------------------------------
    def articles_count(self, obj):
        return obj.articles.count()
    articles_count.short_description = 'تعداد اخبار'

    def keywords_preview(self, obj):
        text = obj.keywords or ''
        return text if len(text) <= 60 else text[:57] + '…'
    keywords_preview.short_description = 'کلمات کلیدی'


# ---------------------------------------------------------------------------
# RSS Feed
# ---------------------------------------------------------------------------
@admin.register(RSSFeed)
class RSSFeedAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'default_category', 'fetch_interval_minutes',
                    'last_fetched_at', 'status_badge')
    list_filter = ('is_active',)
    list_editable = ('is_active', 'fetch_interval_minutes')
    search_fields = ('name', 'url')
    readonly_fields = ('last_fetched_at', 'last_error')
    actions = ['action_fetch_now']

    # -- list_display helpers ------------------------------------------------
    def status_badge(self, obj):
        """Coloured badge summarising feed health for the list view."""
        if not obj.is_active:
            return format_html('<span style="color:#9ca3af">غیرفعال</span>')
        if obj.last_error:
            return format_html('<span style="color:#f87171">خطا</span>')
        return format_html('<span style="color:#34d399">سالم</span>')
    status_badge.short_description = 'وضعیت'

    # -- custom action -------------------------------------------------------
    def action_fetch_now(self, request, queryset):
        """Admin action: fetch the selected feeds right now."""
        created_total = 0
        for feed in queryset:
            created, _ = rss_fetcher.fetch_feed(feed)
            created_total += created
        self.message_user(request, f'{created_total} خبر جدید وارد شد.')
    action_fetch_now.short_description = 'دریافت فیدهای انتخاب‌شده هم‌اکنون'


# ---------------------------------------------------------------------------
# Article
# ---------------------------------------------------------------------------
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'source_badge', 'is_published',
                    'is_featured', 'published_at', 'views_count', 'likes_count')
    list_filter = ('is_published', 'is_featured', 'is_rss', 'category')
    list_editable = ('is_published', 'is_featured')
    search_fields = ('title', 'summary', 'source_name')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    readonly_fields = ('dedup_hash', 'created_at', 'updated_at',
                       'likes_count', 'dislikes_count', 'views_count')

    fieldsets = (
        ('محتوای خبر', {
            'fields': ('title', 'slug', 'summary', 'content', 'category'),
        }),
        ('تصویر', {
            'fields': ('image', 'image_url'),
            'description': 'برای خبر دستی تصویر را آپلود کنید. برای خبر RSS فقط آدرس تصویر استفاده می‌شود.',
        }),
        ('انتشار', {
            'fields': ('is_published', 'is_featured', 'published_at'),
        }),
        ('منبع RSS', {
            'fields': ('is_rss', 'feed', 'source_name', 'source_url'),
            'description': 'این بخش معمولاً برای اخبار وارد‌شده از RSS پر می‌شود.',
        }),
        ('آمار و یکتایی', {
            'classes': ('collapse',),
            'fields': ('dedup_hash', 'likes_count', 'dislikes_count',
                       'views_count', 'created_at', 'updated_at'),
        }),
    )

    def source_badge(self, obj):
        """Show "RSS" + agency name for imported items, otherwise "دستی"."""
        if obj.is_rss:
            return format_html(
                '<span style="color:#a78bfa">RSS · {}</span>',
                obj.source_name or '—',
            )
        return format_html('<span style="color:#93c5fd">دستی</span>')
    source_badge.short_description = 'منبع'
