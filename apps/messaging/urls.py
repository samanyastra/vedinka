from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.messaging.views import MailTemplatesViewSet


router = DefaultRouter()
router.register(r'mail-templates', MailTemplatesViewSet)

urlpatterns = [
    path('', include(router.urls)),
]