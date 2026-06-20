"""
Root URL configuration for the Portale Khabar project.

The admin lives under /admin/ and everything else is delegated to the
feature apps (news, interactions, pages). Keep this file thin: actual
routes are defined in each app's urls.py module.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Persian title for the admin index page.
admin.site.site_header = 'مدیریت پرتال خبری'
admin.site.site_title = 'پرتال خبری'
admin.site.index_title = 'پنل مدیریت'

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public site routes are namespaced per app.
    path('', include('apps.news.urls')),
    path('', include('apps.interactions.urls')),
    path('', include('apps.pages.urls')),
]

# Serve user-uploaded media files during development (DEBUG=True).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
