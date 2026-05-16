from typing import Dict, Any
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.users.serializers import (
    UserProfileSerializer,
    CompleteUserProfileSerializer,
    UpdateUserProfileSerializer,
)
from apps.common.response_serializers import ProfileResponseSerializer
from apps.constants.errors import en as errors
from apps.constants.messages import en as msgs
from apps.common.utils import get_object_or_none
from vedinka.schema_decorators import (
    document_api_view,
    document_create_endpoint,
    document_update_endpoint,
)

User = get_user_model()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@document_api_view(
    operation_id='get_user_profile',
    summary='Get user profile',
    description='Retrieve the authenticated user profile information',
    response_serializer=UserProfileSerializer,
    tags=['Users'],
)
def get_user_profile(request: Request) -> Response:
    """Get current user's profile information."""
    try:
        profile = request.user.profile
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    except Exception as e:
        raise ValidationError({"error": errors.PROFILE_NOT_FOUND}, code=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@document_create_endpoint(
    operation_id='complete_user_profile',
    summary='Complete user profile',
    description='Complete user profile on first login with phone number and additional information',
    request_serializer=CompleteUserProfileSerializer,
    response_serializer=ProfileResponseSerializer,
    tags=['Users'],
)
def complete_user_profile(request: Request) -> Response:
    """Complete user profile on first login."""
    try:
        profile = request.user.profile
        serializer = CompleteUserProfileSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            raise ValidationError(serializer.errors, code=400)
        
        serializer.create(serializer.validated_data)
        profile_data = UserProfileSerializer(profile).data
        
        return Response({
            "message": msgs.PROFILE_COMPLETED,
            "profile": profile_data
        })
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError({"error": str(e)}, code=400)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@document_update_endpoint(
    operation_id='update_user_profile',
    summary='Update user profile',
    description='Update user profile information with partial updates support',
    request_serializer=UpdateUserProfileSerializer,
    response_serializer=ProfileResponseSerializer,
    tags=['Users'],
    partial=True,
)
def update_user_profile(request: Request) -> Response:
    """Update user profile information."""
    try:
        profile = request.user.profile
        serializer = UpdateUserProfileSerializer(
            profile,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            raise ValidationError(serializer.errors, code=400)
        
        serializer.save()
        profile_data = UserProfileSerializer(profile).data
        
        return Response({
            "message": msgs.PROFILE_UPDATED,
            "profile": profile_data
        })
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError({"error": str(e)}, code=400)
