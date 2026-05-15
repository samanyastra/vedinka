from typing import Dict, Any
from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.users.models import UserProfile, UserLanguage, UserGenre
from apps.constants.errors import en as errors

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for complete user profile information."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user_email', 'user_first_name', 'user_last_name',
            'phone_number', 'is_phone_verified', 'is_email_verified',
            'address', 'profile_photo_url', 'profile_photo_thumbnail_url',
            'tagline', 'bio', 'linkedin_url', 'other_social_url',
            'role_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_email', 'user_first_name', 'user_last_name', 
                           'is_phone_verified', 'is_email_verified', 'role_name', 
                           'created_at', 'updated_at']


class CompleteUserProfileSerializer(serializers.Serializer):
    """Serializer for completing user profile on first login."""
    
    phone_number = serializers.CharField(max_length=20, required=True)
    address = serializers.CharField(max_length=500, required=False, allow_blank=True)
    tagline = serializers.CharField(max_length=200, required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    linkedin_url = serializers.URLField(required=False, allow_blank=True)
    other_social_url = serializers.URLField(required=False, allow_blank=True)
    
    def validate_phone_number(self, value: str) -> str:
        """Validate phone number is not already in use."""
        if UserProfile.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(errors.DUPLICATE_PHONE_NUMBER)
        return value
    
    def create(self, validated_data: Dict[str, Any]) -> UserProfile:
        """Update user profile with provided data."""
        user = self.context['request'].user
        profile = user.profile
        
        for field, value in validated_data.items():
            setattr(profile, field, value)
        
        profile.save()
        return profile


class UpdateUserProfileSerializer(serializers.Serializer):
    """Serializer for updating user profile information."""
    
    phone_number = serializers.CharField(max_length=20, required=False)
    address = serializers.CharField(max_length=500, required=False, allow_blank=True)
    profile_photo_url = serializers.URLField(required=False, allow_blank=True)
    profile_photo_thumbnail_url = serializers.URLField(required=False, allow_blank=True)
    tagline = serializers.CharField(max_length=200, required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    linkedin_url = serializers.URLField(required=False, allow_blank=True)
    other_social_url = serializers.URLField(required=False, allow_blank=True)
    
    def validate_phone_number(self, value: str) -> str:
        """Validate phone number is not already in use by another user."""
        user = self.context['request'].user
        if UserProfile.objects.filter(phone_number=value).exclude(user=user).exists():
            raise serializers.ValidationError(errors.DUPLICATE_PHONE_NUMBER)
        return value
    
    def update(self, instance: UserProfile, validated_data: Dict[str, Any]) -> UserProfile:
        """Update user profile with provided data."""
        for field, value in validated_data.items():
            setattr(instance, field, value)
        
        instance.save()
        return instance
