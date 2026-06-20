"""
Admin configuration for the interactions app (comments & votes).

Comment moderation is the most common task, so the CommentAdmin is tuned for
fast approve/reject via both list_editable and a bulk action.
"""

from django.contrib import admin

from .models import Comment, Like


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('short_body', 'name', 'article_link', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    list_editable = ('is_approved',)
    search_fields = ('name', 'email', 'body', 'article__title')
    date_hierarchy = 'created_at'
    actions = ['action_approve', 'action_reject']

    # -- list_display helpers ------------------------------------------------
    def short_body(self, obj):
        text = obj.body or ''
        return text if len(text) <= 80 else text[:77] + '…'
    short_body.short_description = 'متن نظر'

    def article_link(self, obj):
        # Plain text link to the related article title (kept simple on purpose).
        return str(obj.article.title) if obj.article_id else '—'
    article_link.short_description = 'خبر'

    # -- moderation actions --------------------------------------------------
    def action_approve(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} نظر تأیید شد.')
    action_approve.short_description = 'تأیید نظرات انتخاب‌شده'

    def action_reject(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} نظر رد شد.')
    action_reject.short_description = 'رد نظرات انتخاب‌شده'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('article', 'get_value_display_label', 'token_short', 'updated_at')
    list_filter = ('value',)
    search_fields = ('article__title', 'token')
    readonly_fields = ('token', 'created_at', 'updated_at')

    def get_value_display_label(self, obj):
        return obj.get_value_display()
    get_value_display_label.short_description = 'نوع رای'

    def token_short(self, obj):
        return (obj.token or '')[:8] + '…'
    token_short.short_description = 'شناسه'
