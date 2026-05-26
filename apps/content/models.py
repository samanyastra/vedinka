from django.db import models
from django.conf import settings
from apps.users.models import UserProfile
from apps.common.models import Language, Genre, BaseModel


def book_file_path(instance, filename):
    """Generate file path for book PDF: author_id/book_name_id/book_id_file.pdf"""
    return f"{instance.author.id}/{instance.id}/{instance.id}_file.pdf"


def book_thumbnail_path(instance, filename):
    """Generate file path for book thumbnail: author_id/book_name_id/book_id_thumb.jpeg"""
    return f"{instance.author.id}/{instance.id}/{instance.id}_thumb.jpeg"


def book_cover_path(instance, filename):
    """Generate file path for book cover: author_id/book_name_id/book_id_cover.jpeg"""
    return f"{instance.author.id}/{instance.id}/{instance.id}_cover.jpeg"


def book_index_path(instance, filename):
    """Generate file path for book index: author_id/book_name_id/book_id_index.pdf"""
    return f"{instance.author.id}/{instance.id}/{instance.id}_index.pdf"


def book_sample_path(instance, filename):
    """Generate file path for book sample: author_id/book_name_id/book_id_sample.pdf"""
    return f"{instance.author.id}/{instance.id}/{instance.id}_sample.pdf"


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
        upload_to=book_file_path,
        help_text="Original PDF file (< 20MB)"
    )
    cover_image_url = models.FileField(
        upload_to=book_cover_path,
        help_text="Book cover image"
    )
    thumbnail_url = models.FileField(
        upload_to=book_thumbnail_path,
        blank=True,
        null=True,
        help_text="Book thumbnail image"
    )
    sample_read_url = models.FileField(
        upload_to=book_sample_path,
        blank=True,
        null=True,
        help_text="Sample PDF for preview"
    )
    index_file_url = models.FileField(
        upload_to=book_index_path,
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


class BookRecommendation(BaseModel):
    """Book recommendations - for recommended books API"""
    RECOMMENDATION_TYPE_CHOICES = [
        ('similar', 'Similar Books'),
        ('author', 'Other Books by Author'),
        ('genre', 'Same Genre'),
        ('trending', 'Trending Now'),
        ('curated', 'Curated Pick'),
        ('seasonal', 'Seasonal Recommendation'),
        ('custom', 'Custom Recommendation'),
    ]
    
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='recommendations',
        help_text="Book being recommended from"
    )
    recommended_book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='recommended_from',
        help_text="Book being recommended to"
    )
    recommendation_type = models.CharField(
        max_length=50,
        choices=RECOMMENDATION_TYPE_CHOICES,
        default='similar',
        help_text="Type of recommendation"
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.5,
        help_text="Recommendation score (0-1.0)"
    )
    display_order = models.IntegerField(
        default=0,
        help_text="Order in which to display recommendation"
    )
    reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for recommendation"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this recommendation active?"
    )
    
    class Meta:
        ordering = ['-score', 'display_order']
        unique_together = ('book', 'recommended_book')
        indexes = [
            models.Index(fields=['book', '-score']),
            models.Index(fields=['recommendation_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.book.title} → {self.recommended_book.title} ({self.get_recommendation_type_display()})"


class BookPopularity(BaseModel):
    """Monthly popularity metrics per book"""
    POPULARITY_STATUS_CHOICES = [
        ('trending', 'Trending'),
        ('popular', 'Popular'),
        ('moderate', 'Moderate'),
        ('new', 'New Release'),
    ]
    
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='popularity_metrics'
    )
    month = models.DateField(help_text="First day of the month (YYYY-MM-01)")
    sales_count = models.IntegerField(default=0, help_text="Units sold this month")
    view_count = models.IntegerField(default=0, help_text="Page views this month")
    rating_count = models.IntegerField(default=0, help_text="Number of ratings")
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        help_text="Average rating"
    )
    popularity_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Calculated popularity score (0-100)"
    )
    rank = models.IntegerField(
        null=True,
        blank=True,
        help_text="Rank among all books for this month"
    )
    popularity_status = models.CharField(
        max_length=20,
        choices=POPULARITY_STATUS_CHOICES,
        default='moderate',
        help_text="Status based on popularity"
    )
    
    class Meta:
        ordering = ['-month', 'rank']
        unique_together = ('book', 'month')
        indexes = [
            models.Index(fields=['book', '-month']),
            models.Index(fields=['-month', 'rank']),
            models.Index(fields=['popularity_status']),
        ]
    
    def __str__(self):
        return f"{self.book.title} - {self.month.strftime('%B %Y')} (Rank: {self.rank})"


class BookUploadRequest(BaseModel):
    """Admin approval requests for book uploads"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    book = models.OneToOneField(
        Book,
        on_delete=models.CASCADE,
        related_name='upload_request',
        help_text="Reference to the uploaded book"
    )
    author = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='book_upload_requests',
        help_text="Author who uploaded the book"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the request"
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the book was submitted"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_upload_requests',
        help_text="Admin who reviewed the request"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the request was reviewed"
    )
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for rejection (if rejected)"
    )
    admin_comments = models.TextField(
        blank=True,
        null=True,
        help_text="Additional comments from admin"
    )
    
    class Meta:
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['status', '-submitted_at']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['reviewed_by', '-reviewed_at']),
        ]
    
    def __str__(self):
        return f"{self.book.title} - {self.get_status_display()}"
