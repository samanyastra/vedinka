"""
Serializers for user subscription management.
User-facing endpoints for viewing and purchasing subscriptions.
"""
from typing import Dict, Any
from rest_framework import serializers
from datetime import datetime, timedelta

from apps.users.models import SubscriptionType, UserSubscription, SubscriptionOrder, UserProfile
from apps.constants.errors import en as errors


class AvailableSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for available subscription types with purchase status."""
    is_purchased = serializers.SerializerMethodField()
    current_subscription = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionType
        fields = ['id', 'name', 'cost', 'currency', 'duration_in_days', 'features', 'is_purchased', 'current_subscription']
    
    def get_is_purchased(self, obj) -> bool:
        """Check if user has purchased this subscription."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        user_profile = request.user.profile
        return UserSubscription.objects.filter(
            user=user_profile,
            subscription_type=obj,
            valid_till__gt=datetime.now()
        ).exists()
    
    def get_current_subscription(self, obj) -> Dict[str, Any]:
        """Get current subscription details if purchased."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        user_profile = request.user.profile
        subscription = UserSubscription.objects.filter(
            user=user_profile,
            subscription_type=obj,
            valid_till__gt=datetime.now()
        ).first()
        
        if subscription:
            return {
                'id': str(subscription.id),
                'subscribed_at': subscription.subscribed_at,
                'valid_till': subscription.valid_till,
            }
        return None


class UserSubscriptionDetailSerializer(serializers.ModelSerializer):
    """Serializer for user's current subscription details."""
    subscription_name = serializers.CharField(source='subscription_type.name', read_only=True)
    subscription_cost = serializers.DecimalField(
        source='subscription_type.cost',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    subscription_duration = serializers.IntegerField(
        source='subscription_type.duration_in_days',
        read_only=True
    )
    subscription_features = serializers.CharField(
        source='subscription_type.features',
        read_only=True
    )
    is_active = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'subscription_name', 'subscription_cost', 'subscription_duration',
            'subscription_features', 'subscribed_at', 'valid_till', 'is_active', 'days_remaining'
        ]
        read_only_fields = fields
    
    def get_is_active(self, obj) -> bool:
        """Check if subscription is still active."""
        return obj.valid_till > datetime.now()
    
    def get_days_remaining(self, obj) -> int:
        """Calculate days remaining in subscription."""
        if obj.valid_till > datetime.now():
            return (obj.valid_till - datetime.now()).days
        return 0


class CreateSubscriptionOrderSerializer(serializers.Serializer):
    """Serializer for creating subscription orders."""
    subscription_type_id = serializers.UUIDField()
    
    def validate_subscription_type_id(self, value):
        """Validate subscription type exists."""
        try:
            SubscriptionType.objects.get(id=value)
        except SubscriptionType.DoesNotExist:
            raise serializers.ValidationError(errors.SUBSCRIPTION_TYPE_NOT_FOUND)
        return value


class VerifyPaymentSerializer(serializers.Serializer):
    """Serializer for verifying Razorpay payment."""
    razorpay_order_id = serializers.CharField(max_length=100)
    razorpay_payment_id = serializers.CharField(max_length=100)
    razorpay_signature = serializers.CharField(max_length=255)


class SubscriptionOrderResponseSerializer(serializers.ModelSerializer):
    """Serializer for subscription order response."""
    subscription_name = serializers.CharField(source='subscription_type.name', read_only=True)
    
    class Meta:
        model = SubscriptionOrder
        fields = [
            'id', 'razorpay_order_id', 'subscription_name', 'amount',
            'currency', 'payment_status', 'created_at'
        ]
        read_only_fields = fields
