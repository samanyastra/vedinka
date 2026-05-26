"""
URL configuration for content management endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.content.views import BookViewSet

router = DefaultRouter()
router.register(r'books', BookViewSet, basename='book')

urlpatterns = [
    path('', include(router.urls)),
]
