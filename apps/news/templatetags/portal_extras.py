"""
Custom template tags and filters for the Portale Khabar project.

Usage in templates:
    {% load portal_extras %}
    {% portal_date_choices %}
    {{ article.published_at|jalali_date:"d F Y" }}
    {{ article.published_at|jalali_date:"j M Y، ساعت H:i" }}
"""

import jdatetime
from django import template

register = template.Library()


@register.simple_tag
def portal_date_choices():
    """Return date-range filter options as (value, label) pairs."""
    return [
        ('today', 'امروز'),
        ('week', 'این هفته'),
        ('month', 'این ماه'),
    ]


@register.filter
def jalali_date(value, fmt='j F Y'):
    """Convert a Python datetime to a Jalali (Shamsi) date string.

    Uses a format string similar to ``date`` filter:
        j  = day without leading zero
        d  = day with leading zero
        F  = full Persian month name
        Y  = 4-digit year
        H  = hour, i = minute, s = second
    """
    if value is None:
        return ''
    try:
        jdt = jdatetime.fromgregorian(
            date=value.date() if hasattr(value, 'date') else value,
            time=value.time() if hasattr(value, 'time') else None,
        )
        return jdt.strftime(fmt)
    except (ValueError, AttributeError, TypeError):
        return ''
