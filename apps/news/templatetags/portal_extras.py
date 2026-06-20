"""
Custom template tags and filters for the Portale Khabar project.

Usage in templates:
    {% load portal_extras %}
    {% portal_date_choices %}
"""

from django import template

register = template.Library()


@register.simple_tag
def portal_date_choices():
    """
    Return the date-range filter options as a list of ``(value, label)`` pairs.

    Consumed by the ``partials/filter_bar.html`` template to render date pills.
    """
    return [
        ('today', 'امروز'),
        ('week', 'این هفته'),
        ('month', 'این ماه'),
    ]
