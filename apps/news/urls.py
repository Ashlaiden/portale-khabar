"""
URL routes for the public news site.

All routes here use the ``news:`` namespace so templates can reference them
with ``{% url 'news:detail' slug=... %}``.

NOTE: We use ``re_path`` for slug-based routes because Django's built-in
``<slug:slug>`` converter only accepts ASCII characters, but our slugs
contain Persian text (generated with ``slugify(..., allow_unicode=True)``).
"""

from django.urls import path, re_path

from . import views

app_name = 'news'

# Unicode-aware slug pattern: Persian + ASCII word characters and hyphens.
# ``\w`` with re.UNICODE (default in Py3) matches Persian letters too.
SLUG_RE = r'(?P<slug>[\w-]+)'

urlpatterns = [
    # Home page (featured boxes + latest news + sidebar).
    path('', views.home, name='home'),

    # News listing with filters (category / date / search).
    path('news/', views.news_list, name='list'),
    re_path(r'^news/category/' + SLUG_RE + r'/$', views.news_list, name='category'),
    path('rss-news/', views.rss_news_list, name='rss_news'),
    path('search/', views.search, name='search'),

    # Single article detail (with comments + like buttons).
    re_path(r'^news/' + SLUG_RE + r'/$', views.news_detail, name='detail'),
]
