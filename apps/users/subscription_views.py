"""
Subscription management views - Admin only.
Only accessible to Django superusers or users with IsAdmin permission.
"""
from typing import Dict, Any
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
from rest_framework import status

from apps.users.models import SubscriptionType, UserSubscription
from apps.users.subscription_serializers import (
    SubscriptionTypeSerializer,
    CreateSubscriptionTypeSerializer,
    UpdateSubscriptionTypeSerializer,
    UserSubscriptionSerializer,
    CreateUserSubscriptionSerializer,
    UpdateUserSubscriptionSerializer,
)
from apps.common.response_serializers import SuccessResponseSerializer
from apps.auth.permissions import IsSuperUserOrAdmin
from apps.common.utils import get_object_or_none
from drf_spectacular.utils import extend_schema, OpenApiResponse


def check_admin_permission(request: Request) -> None:
    """Check if user is admin or superuser.
    
    Args:
        request: HTTP request object
        
    Raises:
        PermissionDenied: If user is not admin or superuser
    """
    if not (request.user.is_superuser or 
            (request.user.profile and request.user.profile.role and 
             request.user.profile.role.name == 'admin')):
        raise PermissionDenied("Only admins can access this endpoint")


# ============================================================================
# SUBSCRIPTION TYPE ENDPOINTS
# ============================================================================

@extend_schema(
    operation_id='list_subscription_types',
    summary='List all subscription types',
    description='Get all available subscription types (Admin only)',
    responses={200: SubscriptionTypeSerializer(many=True)},
    tags=['Subscriptions - Admin'],
)
@api_view(["GET"])
@permission_classes([IsSuperUserOrAdmin])
def list_subscription_types(request: Request) -> Response:
    """List all subscription types."""
    subscriptions = SubscriptionType.objects.all()
    serializer = SubscriptionTypeSerializer(subscriptions, many=True)
    return Response(serializer.data)


@extend_schema(
    operation_id='retrieve_subscription_type',
    summary='Get subscription type details',
    description='Get details of a specific subscription type (Admin only)',
    responses={200: SubscriptionTypeSerializer},
    tags=['Subscriptions - Admin'],
)
@api_view(["GET"])
@permission_classes([IsSuperUserOrAdmin])
def get_subscription_type(request: Request, subscription_id: str) -> Response:
    """Get subscription type details."""
    subscription = get_object_or_none(SubscriptionType, id=subscription_id)
    if not subscription:
        raise ValidationError({"error": "Subscription type not found"}, code=404)
    
    serializer = SubscriptionTypeSerializer(subscription)
    return Response(serializer.data)


@extend_schema(
    operation_id='create_subscription_type',
    summary='Create subscription type',
    description='Create a new subscription type (Admin only)',
    request=CreateSubscriptionTypeSerializer,
    responses={201: SubscriptionTypeSerializer},
    tags=['Subscriptions - Admin'],
)
@api_view(["POST"])
@permission_classes([IsSuperUserOrAdmin])
def create_subscription_type(request: Request) -> Response:
    """Create new subscription type."""
    serializer = CreateSubscriptionTypeSerializer(data=request.data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors, code=400)
    
    subscription = serializer.save()
    response_serializer = SubscriptionTypeSerializer(subscription)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    operation_id='update_subscription_type',
    summary='Update subscription type',
    description='Update an existing subscription type (Admin only)',
    request=UpdateSubscriptionTypeSerializer,
    responses={200: SubscriptionTypeSerializer},
    tags=['Subscriptions - Admin'],
)
@api_view(["PATCH"])
@permission_classes([IsSuperUserOrAdmin])
def update_subscription_type(request: Request, subscription_id: str) -> Response:
    """Update subscription type."""
    subscription = get_object_or_none(SubscriptionType, id=subscription_id)
    if not subscription:
        raise ValidationError({"error": "Subscription type not found"}, code=404)
    
    serializer = UpdateSubscriptionTypeSerializer(
        data=request.data,
        context={'subscription_id': subscription_id}
    )
    if not serializer.is_valid():
        raise ValidationError(serializer.errors, code=400)
    
    subscription = serializer.update(subscription, serializer.validated_data)
    response_serializer = SubscriptionTypeSerializer(subscription)
    return Response(response_serializer.data)


@extend_schema(
    operation_id='delete_subscription_type',
    summary='Delete subscription type',
    description='Delete a subscription type (Admin only)',
    request=None,
    responses={200: SuccessResponseSerializer},
    tags=['Subscriptions - Admin'],
)
@api_view(["DELETE"])
@permission_classes([IsSuperUserOrAdmin])
def delete_subscription_type(request: Request, subscription_id: str) -> Response:
    """Delete subscription type."""
    subscription = get_object_or_none(SubscriptionType, id=subscription_id)
    if not subscription:
        raise ValidationError({"error": "Subscription type not found"}, code=404)
    
    subscription.delete()
    return Response({"status": True, "message": "Subscription type deleted successfully"})


# ============================================================================
# USER SUBSCRIPTION ENDPOINTS
# ============================================================================

@extend_schema(
    operation_id='list_user_subscriptions',
    summary='List all user subscriptions',
    description='Get all user subscriptions (Admin only)',
    responses={200: UserSubscriptionSerializer(many=True)},
    tags=['Subscriptions - Admin'],
)
@api_view(["GET"])
@permission_classes([IsSuperUserOrAdmin])
def list_user_subscriptions(request: Request) -> Response:
    """List all user subscriptions."""
    subscriptions = UserSubscription.objects.all()
    serializer = UserSubscriptionSerializer(subscriptions, many=True)
    return Response(serializer.data)


@extend_schema(
    operation_id='retrieve_user_subscription',
    summary='Get user subscription details',
    description='Get details of a specific user subscription (Admin only)',
    responses={200: UserSubscriptionSerializer},
    tags=['Subscriptions - Admin'],
)
@api_view(["GET"])
@permission_classes([IsSuperUserOrAdmin])
def get_user_subscription(request: Request, subscription_id: str) -> Response:
    """Get user subscription details."""
    subscription = get_object_or_none(UserSubscription, id=subscription_id)
    if not subscription:
        raise ValidationError({"error": "User subscription not found"}, code=404)
    
    serializer = UserSubscriptionSerializer(subscription)
    return Response(serializer.data)


@extend_schema(
    operation_id='assign_subscription_to_user',
    summary='Assign subscription to user',
    description='Assign a subscription type to a user (Admin only)',
    request=CreateUserSubscriptionSerializer,
    responses={201: UserSubscriptionSerializer},
    tags=['Subscriptions - Admin'],
)
@api_view(["POST"])
@permission_classes([IsSuperUserOrAdmin])
def assign_subscription_to_user(request: Request) -> Response:
    """Assign subscription to user."""
    serializer = CreateUserSubscriptionSerializer(data=request.data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors, code=400)
    
    subscription = serializer.save()
    response_serializer = UserSubscriptionSerializer(subscription)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    operation_id='update_user_subscription',
    summary='Update user subscription',
    description='Update a user subscription (Admin only)',
    request=UpdateUserSubscriptionSerializer,
    responses={200: UserSubscriptionSerializer},
    tags=['Subscriptions - Admin'],
)
@api_view(["PATCH"])
@permission_classes([IsSuperUserOrAdmin])
def update_user_subscription(request: Request, subscription_id: str) -> Response:
    """Update user subscription."""
    subscription = get_object_or_none(UserSubscription, id=subscription_id)
    if not subscription:
        raise ValidationError({"error": "User subscription not found"}, code=404)
    
    serializer = UpdateUserSubscriptionSerializer(data=request.data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors, code=400)
    
    subscription = serializer.update(subscription, serializer.validated_data)
    response_serializer = UserSubscriptionSerializer(subscription)
    return Response(response_serializer.data)


@extend_schema(
    operation_id='delete_user_subscription',
    summary='Delete user subscription',
    description='Delete a user subscription (Admin only)',
    request=None,
    responses={200: SuccessResponseSerializer},
    tags=['Subscriptions - Admin'],
)
@api_view(["DELETE"])
@permission_classes([IsSuperUserOrAdmin])
def delete_user_subscription(request: Request, subscription_id: str) -> Response:
    """Delete user subscription."""
    subscription = get_object_or_none(UserSubscription, id=subscription_id)
    if not subscription:
        raise ValidationError({"error": "User subscription not found"}, code=404)
    
    subscription.delete()
    return Response({"status": True, "message": "User subscription deleted successfully"})
