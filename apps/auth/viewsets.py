
from rest_framework import viewsets

from apps.auth.models import TokenTypes
from apps.auth.serializers import TokenTypeSerialzier


class TokenTypesViewset(viewsets.ModelViewSet):
    """ViewSet for CRUD operations on MailTemplates."""
    
    queryset = TokenTypes.objects.all()
    serializer_class = TokenTypeSerialzier
    permission_classes = []
    http_method_names = ['get', 'post', 'put']
