import uuid

from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from apps.common.models import Language, Genre, BaseModel


class User(AbstractUser):
    """Custom user model with UUID primary key."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'


class Role(BaseModel):
    """User roles for authorization and access control"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Permission(BaseModel):
    """Permissions for fine-grained access control"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class RolePermission(BaseModel):
    """Many-to-Many relationship between roles and permissions"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('role', 'permission')
    
    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"


class UserProfile(BaseModel):
    user_model = get_user_model()
    """Extended user profile with additional information"""
    user = models.OneToOneField(user_model, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    address = models.TextField(blank=True, null=True)
    profile_photo_url = models.URLField(blank=True, null=True)
    profile_photo_thumbnail_url = models.URLField(blank=True, null=True)
    tagline = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    other_social_url = models.URLField(blank=True, null=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.role.name if self.role else 'No Role'}"


class UserLanguage(BaseModel):
    """Many-to-Many relationship between users and languages"""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='languages')
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='users')
    
    class Meta:
        unique_together = ('user', 'language')
    
    def __str__(self):
        return f"{self.user.user.username} - {self.language.language_name}"


class UserGenre(BaseModel):
    """Many-to-Many relationship between users and genres"""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='genres')
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, related_name='users')
    
    class Meta:
        unique_together = ('user', 'genre')
    
    def __str__(self):
        return f"{self.user.user.username} - {self.genre.name}"


class SubscriptionType(BaseModel):
    """Subscription plan types available"""
    name = models.CharField(max_length=100, unique=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    duration_in_days = models.IntegerField(help_text="Duration of subscription in days")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['cost']
    
    def __str__(self):
        return f"{self.name} - {self.cost} {self.currency}"


class UserSubscription(BaseModel):
    """User subscription records"""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='subscriptions')
    subscription_type = models.ForeignKey(SubscriptionType, on_delete=models.CASCADE, related_name='subscribers')
    subscribed_at = models.DateTimeField(auto_now_add=True)
    valid_till = models.DateTimeField()
    
    class Meta:
        ordering = ['-valid_till']
    
    def __str__(self):
        return f"{self.user.user.username} - {self.subscription_type.name}"
