from django.contrib import admin
from .models import ContactMessage

# Register your models here.
    
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at', 'is_read')
    list_filter = ('is_read',)
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('name', 'email', 'message', 'created_at')
    date_hierarchy = 'created_at'
    actions = ['mark_as_read']

    @admin.action(description='علامت‌گذاری به عنوان خوانده شده')
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)