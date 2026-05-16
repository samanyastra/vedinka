"""
Serializers for subscription management.
Admin-only endpoints for managing subscription types and user subscriptions.
"""
from typing import Dict, Any
from rest_framework import serializers
from decimal import Decimal

from apps.users.models import SubscriptionType, UserSubscription, UserProfile
from apps.constants.errors import en as errors


class SubscriptionTypeSerializer(serializers.ModelSerializer):
    """Serializer for subscription type management."""
    
    class Meta:
        model = SubscriptionType
        fields = [
            'id', 'name', 'cost', 'currency', 'duration_in_days',
            'features', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreateSubscriptionTypeSerializer(serializers.Serializer):
    """Serializer for creating subscription types."""
    
    name = serializers.CharField(max_length=100)
    cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=10, default='INR')
    duration_in_days = serializers.IntegerField(min_value=1)
    features = serializers.CharField(required=False, allow_blank=True)
    
    def validate_name(self, value: str) -> str:
        """Validate subscription type name is unique."""
        if SubscriptionType.objects.filter(name=value).exists():
            raise serializers.ValidationError(errors.DUPLICATE_SUBSCRIPTION_TYPE)
        return value
    
    def create(self, validated_data: Dict[str, Any]) -> SubscriptionType:
        """Create new subscription type."""
        return SubscriptionType.objects.create(**validated_data)


class UpdateSubscriptionTypeSerializer(serializers.Serializer):
    """Serializer for updating subscription types."""
    
    name = serializers.CharField(max_length=100, required=False)
    cost = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    currency = serializers.CharField(max_length=10, required=False)
    duration_in_days = serializers.IntegerField(min_value=1, required=False)
    features = serializers.CharField(required=False, allow_blank=True)
    
    def validate_name(self, value: str) -> str:
        """Validate subscription type name is unique."""
        subscription_id = self.context.get('subscription_id')
        if SubscriptionType.objects.filter(name=value).exclude(id=subscription_id).exists():
            raise serializers.ValidationError(errors.DUPLICATE_SUBSCRIPTION_TYPE)
        return value
    
    def update(self, instance: SubscriptionType, validated_data: Dict[str, Any]) -> SubscriptionType:
        """Update subscription type."""
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for user subscription records."""
    
    user_email = serializers.CharField(source='user.user.email', read_only=True)
    user_name = serializers.CharField(source='user.user.get_full_name', read_only=True)
    subscription_name = serializers.CharField(source='subscription_type.name', read_only=True)
    subscription_cost = serializers.DecimalField(
        source='subscription_type.cost',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'user_email', 'user_name', 'subscription_name',
            'subscription_cost', 'subscribed_at', 'valid_till',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'user_name', 'subscription_name',
            'subscription_cost', 'subscribed_at', 'created_at', 'updated_at'
        ]


class CreateUserSubscriptionSerializer(serializers.Serializer):
    """Serializer for assigning subscriptions to users."""
    
    user_id = serializers.UUIDField()
    subscription_type_id = serializers.UUIDField()
    valid_till = serializers.DateTimeField()
    
    def validate_user_id(self, value):
        """Validate user exists."""
        try:
            UserProfile.objects.get(user_id=value)
        except UserProfile.DoesNotExist:
            raise serializers.ValidationError(errors.USER_404_ERROR)
        return value
    
    def validate_subscription_type_id(self, value):
        """Validate subscription type exists."""
        try:
            SubscriptionType.objects.get(id=value)
        except SubscriptionType.DoesNotExist:
            raise serializers.ValidationError(errors.SUBSCRIPTION_TYPE_NOT_FOUND)
        return value
    
    def create(self, validated_data: Dict[str, Any]) -> UserSubscription:
        """Create user subscription."""
        user_profile = UserProfile.objects.get(user_id=validated_data['user_id'])
        subscription_type = SubscriptionType.objects.get(id=validated_data['subscription_type_id'])
        
        return UserSubscription.objects.create(
            user=user_profile,
            subscription_type=subscription_type,
            valid_till=validated_data['valid_till']
        )


class UpdateUserSubscriptionSerializer(serializers.Serializer):
    """Serializer for updating user subscriptions."""
    
    valid_till = serializers.DateTimeField(required=False)
    
    def update(self, instance: UserSubscription, validated_data: Dict[str, Any]) -> UserSubscription:
        """Update user subscription."""
        if 'valid_till' in validated_data:
            instance.valid_till = validated_data['valid_till']
            instance.save()
        return instance
