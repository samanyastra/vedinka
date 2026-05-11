from django.shortcuts import render
from rest_framework import viewsets

from apps.messaging.models import MailTemplates
from apps.messaging.serializers import MailTemplatesSerializer


class MailTemplatesViewSet(viewsets.ModelViewSet):
    """ViewSet for CRUD operations on MailTemplates."""

    queryset = MailTemplates.objects.all()
    serializer_class = MailTemplatesSerializer

    def get_queryset(self):
        """Optionally filter by active status."""
        queryset = MailTemplates.objects.all()
        is_active = self.request.query_params.get("is_active", None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset
