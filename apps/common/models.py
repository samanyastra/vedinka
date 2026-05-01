from django.db import models
import uuid


class BaseModel(models.Model):
    """Abstract base model with UUID primary key and timestamps"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Language(BaseModel):
    """Languages supported in the application"""
    language_name = models.CharField(max_length=100)
    language_code = models.CharField(
        max_length=10,
        unique=True,
        help_text="ISO language code (e.g., 'en', 'hi', 'fr')"
    )
    place_used = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        ordering = ['language_name']
    
    def __str__(self):
        return f"{self.language_name} ({self.language_code})"


class Genre(BaseModel):
    """Book genres/categories for classification"""
    name = models.CharField(max_length=100, unique=True)
    usage_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TransactionStatus(BaseModel):
    """Status types for transactions (PENDING, SUCCESS, FAILED, REFUNDED)"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    
    name = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        unique=True
    )
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TransactionCharge(BaseModel):
    """Transaction charges/fees configuration"""
    charge_name = models.CharField(max_length=100)
    charge_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        ordering = ['charge_name']
    
    def __str__(self):
        return f"{self.charge_name} ({self.charge_percentage}%)"


class PromoCode(BaseModel):
    """Promotional codes for discounts"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    min_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Minimum discount amount"
    )
    max_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum discount amount"
    )
    valid_till = models.DateTimeField()
    
    class Meta:
        ordering = ['-valid_till']
    
    def __str__(self):
        return f"{self.code} - {self.name}"



