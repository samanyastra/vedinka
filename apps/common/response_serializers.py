"""
Common response serializers for API endpoints.
Used for Swagger/OpenAPI documentation.
"""
from rest_framework import serializers


class SuccessResponseSerializer(serializers.Serializer):
    """Generic success response serializer."""
    status = serializers.BooleanField()
    message = serializers.CharField(required=False, allow_blank=True)


class UserIdResponseSerializer(serializers.Serializer):
    """Response serializer for user ID."""
    id = serializers.UUIDField()


class LoginResponseSerializer(serializers.Serializer):
    """Response serializer for login endpoint."""
    user = serializers.UUIDField()
    role = serializers.CharField(allow_null=True)
    vedinka_access = serializers.CharField()


class RefreshResponseSerializer(serializers.Serializer):
    """Response serializer for refresh token endpoint."""
    user = serializers.UUIDField()
    role = serializers.CharField(allow_null=True)
    vedinka_access = serializers.CharField()


class LogoutResponseSerializer(serializers.Serializer):
    """Response serializer for logout endpoint."""
    status = serializers.CharField()
    message = serializers.CharField()


class ActivationResponseSerializer(serializers.Serializer):
    """Response serializer for activation endpoint."""
    status = serializers.BooleanField()


class ResendActivationResponseSerializer(serializers.Serializer):
    """Response serializer for resend activation endpoint."""
    status = serializers.BooleanField()
    message = serializers.CharField()


class ProfileResponseSerializer(serializers.Serializer):
    """Response serializer for profile endpoints."""
    message = serializers.CharField()
    profile = serializers.DictField(child=serializers.CharField(), required=False)


class ErrorResponseSerializer(serializers.Serializer):
    """Generic error response serializer."""
    error = serializers.CharField(required=False)
    detail = serializers.CharField(required=False)


class ValidationErrorResponseSerializer(serializers.Serializer):
    """Validation error response serializer."""
    detail = serializers.CharField(required=False)
    error = serializers.CharField(required=False)
