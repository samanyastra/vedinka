from django.db import models
from apps.users.models import UserProfile
from apps.content.models import Book
from apps.common.models import BaseModel


class UserLibrary(BaseModel):
    """User's personal library of purchased/owned books"""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='library')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='in_libraries')
    purchased_at = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(blank=True, null=True, help_text="Expiry date for rental books")
    
    class Meta:
        ordering = ['-purchased_at']
        unique_together = ('user', 'book')
        indexes = [
            models.Index(fields=['user', '-purchased_at']),
            models.Index(fields=['expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.user.user.username} - {self.book.title}"


class UserLibraryPwdBackup(BaseModel):
    """Backup storage for user library password/access tokens"""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='library_pwd_backups')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField()
    password_raw = models.CharField(
        max_length=255,
        help_text="Encrypted password for accessing the book"
    )
    last_retrived_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-purchased_at']
        unique_together = ('user', 'book')
    
    def __str__(self):
        return f"{self.user.user.username} - {self.book.title} (Backup)"
