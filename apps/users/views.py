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
from apps.constants.errors import en as errors
from apps.constants.messages import en as msgs
from apps.common.utils import get_object_or_none

User = get_user_model()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
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
