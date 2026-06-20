"""
URL routes for static-ish pages (about / contact).

The contact page accepts a POST and emails the message; everything else is
rendered from templates.
"""

from django.urls import path

from . import views

app_name = 'pages'

urlpatterns = [
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]
