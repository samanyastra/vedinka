from rest_framework import serializers
from apps.messaging.models import MailTemplates


class MailTemplatesSerializer(serializers.ModelSerializer):
    """Serializer for MailTemplates model with CRUD operations."""
    
    class Meta:
        model = MailTemplates
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']