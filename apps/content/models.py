from django.db import models
from apps.users.models import UserProfile
from apps.common.models import Language, Genre, BaseModel


class Category(BaseModel):
    """Book categories"""
    name = models.CharField(max_length=100, unique=True)
    short_description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name


class Subcategory(BaseModel):
    """Subcategories within each category"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    short_description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name_plural = 'Subcategories'
        unique_together = ('category', 'name')
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Tag(BaseModel):
    """Tags for books"""
    name = models.CharField(max_length=100, unique=True)
    usage_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Book(BaseModel):
    """Books in the platform"""
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='books_authored')
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, related_name='books')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='books')
    subcategory = models.ForeignKey(Subcategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    is_checks_passed = models.BooleanField(default=False, help_text="Whether the book passed all quality checks")
    short_description = models.TextField()
    full_description = models.TextField()
    number_of_pages = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_file_url = models.FileField(
        upload_to='books/',
        help_text="Original PDF file (< 20MB)"
    )
    cover_image_url = models.URLField()
    sample_read_url = models.FileField(
        upload_to='book_samples/',
        blank=True,
        null=True,
        help_text="Sample PDF for preview"
    )
    index_file_url = models.FileField(
        upload_to='book_indexes/',
        blank=True,
        null=True,
        help_text="Book index/TOC PDF"
    )
    purchase_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['category']),
            models.Index(fields=['is_checks_passed']),
        ]
    
    def __str__(self):
        return self.title


class BookTag(BaseModel):
    """Many-to-Many relationship between books and tags"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='tags_relation')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='books')
    
    class Meta:
        unique_together = ('book', 'tag')
    
    def __str__(self):
        return f"{self.book.title} - {self.tag.name}"


class BookGenre(BaseModel):
    """Many-to-Many relationship between books and genres"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='genres_relation')
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, related_name='books')
    
    class Meta:
        unique_together = ('book', 'genre')
    
    def __str__(self):
        return f"{self.book.title} - {self.genre.name}"
