"""
URL routes for user interactions (comments and likes).

These endpoints are designed to be called via AJAX from ``main.js``. Comment
submission falls back to a normal form POST (no JS) so the site still works
without JavaScript.
"""

from django.urls import path

from . import views

app_name = 'interactions'

urlpatterns = [
    # POST a new comment on an article.
    path('comment/<int:article_id>/', views.add_comment, name='add_comment'),

    # AJAX: toggle like / dislike on an article.
    path('like/<int:article_id>/', views.toggle_like, name='toggle_like'),
]
