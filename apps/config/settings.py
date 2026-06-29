"""
Django settings for the Portale Khabar (news portal) project.

Key design choices (see the project plan):
  * SQLite database (no external DB server required).
  * Persian (fa) locale and Asia/Tehran timezone, RTL UI.
  * django-jazzmin for a modern, dark, RTL admin skin.
  * django-apscheduler for periodic background RSS fetching inside the
    Django process (no Celery / separate worker required).
  * django-render-block for rendering individual template blocks over AJAX
    (used by the like and comment features).

Most tunable values are grouped at the bottom of this file so the project
is easy to reconfigure without hunting through the rest of the settings.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Base paths
# ---------------------------------------------------------------------------

# Project root: the folder that contains manage.py (two levels up from this file).
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Security & debugging
# ---------------------------------------------------------------------------
# NOTE: Replace SECRET_KEY and review DEBUG/ALLOWED_HOSTS before going to
# production. These development defaults are fine for a local academic project.
SECRET_KEY = 'django-insecure-change-me-this-is-a-local-development-key-only'

DEBUG = True

ALLOWED_HOSTS = ['*']


# ---------------------------------------------------------------------------
# Application registry
# ---------------------------------------------------------------------------
# Order matters only for apps that override admin templates (jazzmin must come
# BEFORE django.contrib.admin so its templates take precedence).
INSTALLED_APPS = [
    'jazzmin',  # Modern admin skin (must precede admin)

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'django_apscheduler',        # Background scheduler for RSS jobs
    # NOTE: django-render-block is a library (imported as `render_block`),
    # not a Django app, so it is intentionally NOT added to INSTALLED_APPS.

    # Local apps (see apps/ package)
    'apps.news',
    'apps.interactions',
    'apps.pages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'apps.config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Template lookup directories: root-level templates/ folder.
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Expose a few site-wide values (categories, current year, etc.)
                # to every template via this custom context processor.
                'apps.news.context_processors.site_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'apps.config.wsgi.application'
ASGI_APPLICATION = 'apps.config.asgi.application'


# ---------------------------------------------------------------------------
# Database (SQLite as required)
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ---------------------------------------------------------------------------
# Internationalisation: Persian / RTL
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'fa'           # Persian
TIME_ZONE = 'Asia/Tehran'      # Local time for the target audience
USE_I18N = True
USE_TZ = True

# Default for new auto-fields (Django 3.2+).
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------------------------
# Static & media files
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'

# Tailwind-compiled CSS, JS, fonts, etc. are collected here on collectstatic.
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Additional static source folders searched by the staticfiles finder.
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Uploaded images (manual article images).
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ---------------------------------------------------------------------------
# django-apscheduler: background RSS fetching
# ---------------------------------------------------------------------------
# Stores scheduler job executions in the DB so they are visible in the admin.
APSCHEDULER_DATETIME_FORMAT = 'N j, Y, f:s a'
APSCHEDULER_RUN_NOW_TIMEOUT = 25  # seconds


# ---------------------------------------------------------------------------
# django-jazzmin: modern RTL admin skin
# ---------------------------------------------------------------------------
# A consolidated config block that makes the admin Persian-first, RTL and dark.
JAZZMIN_SETTINGS = {
    # Brand shown in the top navbar / login.
    'site_title': 'پرتال خبری',
    'site_header': 'مدیریت پرتال خبری',
    'site_brand': 'پرتال خبری',
    'site_logo_classes': 'hide-on-mobile',
    'welcome_sign': 'به پنل مدیریت خوش آمدید',
    'copyright': 'پرتال خبری',
    # Search field visible in the navbar.
    'search_model': ['news.Article', 'news.RSSFeed'],
    # User avatar / icons.
    'user_avatar': None,
    # Top navigation menu.
    'topmenu_links': [
        {'name': 'داشبورد', 'url': 'admin:index', 'permissions': ['auth.view_user']},
        {'name': 'مقالات', 'url': 'admin:news_article_changelist', 'icon': 'fa fa-newspaper'},
        {'name': 'دسته‌بندی‌ها', 'url': 'admin:news_category_changelist', 'icon': 'fa fa-tags'},
        {'name': 'منابع RSS', 'url': 'admin:news_rssfeed_changelist', 'icon': 'fa fa-rss'},
        {'name': 'نظرات', 'url': 'admin:interactions_comment_changelist', 'icon': 'fa fa-comments'},
        {'model': 'auth.User'},
    ],
    # Left sidebar user menu.
    'usermenu_links': [
        {'name': 'تغییر رمز عبور', 'url': 'admin:password_change', 'icon': 'fa fa-key'},
        {'name': 'خروج', 'url': 'admin:logout', 'icon': 'fa fa-sign-out'},
    ],
    # Show the "recent actions" sidebar.
    'show_ui_builder': False,
    # Modern dark / flat theme by default.
    'changeform_format': 'horizontal_tabs',
    # Icon per app/model (FontAwesome free names).
    'icons': {
        'news.Article': 'fa fa-newspaper',
        'news.Category': 'fa fa-tags',
        'news.RSSFeed': 'fa fa-rss',
        'interactions.Comment': 'fa fa-comments',
        'interactions.Like': 'fa fa-thumbs-up',
        'auth.User': 'fa fa-user',
        'auth.Group': 'fa fa-users',
    },
}

# A modern dark theme for jazzmin (uses the bundled "darkly" theme variant).
JAZZMIN_UI_TWEAK = {
    'navbar_small_text': False,
    'footer_small_text': False,
    'body_small_text': False,
    'brand_small_text': False,
    'brand_colour': 'navbar-indigo',
    'accent': 'accent-primary',
    'navbar': 'navbar-dark navbar-primary',
    'no_navbar_border': True,
    'navbar_fixed': True,
    'layout_boxed': False,
    'footer_fixed': False,
    'sidebar_fixed': True,
    'sidebar': 'sidebar-dark-primary',
    'sidebar_nav_small_text': False,
    'sidebar_disable_expand': False,
    'sidebar_child_indent': False,
    'sidebar_compact': False,
    'sidebar_flat_style': True,
    # Use the dark "darkly" theme.
    'theme': 'darkly',
    'dark_mode_theme': 'darkly',
}


# ---------------------------------------------------------------------------
# Project-specific tunables
# ---------------------------------------------------------------------------
# Number of "latest news" items shown in the left sidebar widget.
NEWS_SIDEBAR_COUNT = 10

# Number of featured big boxes on the home page.
NEWS_FEATURED_COUNT = 3

# Default page size for the news list views.
NEWS_PAGE_SIZE = 12

# Default fetch interval (minutes) for newly-created RSS feeds.
RSS_DEFAULT_INTERVAL_MINUTES = 5

# How many items to keep per feed (oldest beyond this are pruned automatically
# to keep the DB tidy). Set to 0 to disable pruning.
RSS_MAX_ITEMS_PER_FEED = 200

# Session key used to persist the per-browser vote identity for likes/dislikes.
LIKE_SESSION_KEY = '_like_token'
