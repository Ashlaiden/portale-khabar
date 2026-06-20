"""
Views for the static-ish pages: 'About' and 'Contact'.

The contact page accepts a POST of a simple message form. By default it does
not actually send email (to avoid requiring an SMTP server in a university
project) – instead it saves the message in the Django messages framework so
the user sees a confirmation. Flip ``CONTACT_EMAIL_ENABLED`` and configure
``EMAIL_HOST_*`` in settings to enable real email delivery.
"""

import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

# Toggle: set to True (and configure SMTP) in settings to actually send email.
CONTACT_EMAIL_ENABLED = getattr(settings, 'CONTACT_EMAIL_ENABLED', False)


def about(request):
    """Render the 'About us' page."""
    return render(request, 'pages/about.html', {'active_menu': 'about'})


@csrf_protect
@require_http_methods(['GET', 'POST'])
def contact(request):
    """
    Render the 'Contact us' page and accept submissions of the contact form.

    GET  -> show the (empty) form.
    POST -> validate, optionally email the message, show a success message.
    """
    if request.method != 'POST':
        return render(request, 'pages/contact.html', {'active_menu': 'contact'})

    name = (request.POST.get('name') or '').strip()
    email = (request.POST.get('email') or '').strip()
    message = (request.POST.get('message') or '').strip()

    if not name or not message:
        messages.error(request, 'نام و متن پیام الزامی هستند.')
        # Re-render with submitted values so the user doesn't lose typing.
        return render(request, 'pages/contact.html', {
            'active_menu': 'contact',
            'form_name': name,
            'form_email': email,
            'form_message': message,
        })

    if CONTACT_EMAIL_ENABLED:
        try:
            send_mail(
                subject=f'پیام از {name}',
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', email or 'no-reply@example.com'),
                recipient_emails=[getattr(settings, 'CONTACT_EMAIL', 'admin@example.com')],
                fail_silently=True,
            )
        except Exception:  # pragma: no cover - email failures shouldn't crash UX
            logger.exception('Failed to send contact email.')

    messages.success(request, 'پیام شما با موفقیت ارسال شد. متشکریم!')
    return redirect('pages:contact')
