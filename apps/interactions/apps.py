"""App configuration for the `interactions` app (comments & likes)."""

from django.apps import AppConfig


class InteractionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.interactions'
    verbose_name = 'تعاملات کاربران'
