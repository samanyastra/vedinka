from rest_framework import serializers
from apps.content.models import Book, BookPopularity, BookRecommendation
from typing import List, Dict, Any


class FeaturedBookSerializer(serializers.ModelSerializer):
    """Serializer for featured books using Book model."""
    author_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    cover_image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    def get_author_name(self, obj) -> str:
        return obj.author.user.get_full_name() or obj.author.user.username
    
    def get_cover_image_url(self, obj):
        return obj.cover_image_url.url if obj.cover_image_url else None
    
    def get_thumbnail_url(self, obj):
        return obj.thumbnail_url.url if obj.thumbnail_url else None
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'subtitle', 'author_name', 'category_name',
            'price', 'short_description', 'cover_image_url', 'thumbnail_url',
            'purchase_count', 'created_at'
        ]


class PopularBookSerializer(serializers.ModelSerializer):
    """Serializer for popular books from BookPopularity."""
    book_id = serializers.CharField(source='book.id', read_only=True)
    title = serializers.CharField(source='book.title', read_only=True)
    subtitle = serializers.CharField(source='book.subtitle', read_only=True, allow_null=True)
    author_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='book.category.name', read_only=True, allow_null=True)
    price = serializers.DecimalField(source='book.price', max_digits=10, decimal_places=2, read_only=True)
    short_description = serializers.CharField(source='book.short_description', read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    def get_author_name(self, obj) -> str:
        return obj.book.author.user.get_full_name() or obj.book.author.user.username
    
    def get_cover_image_url(self, obj):
        return obj.book.cover_image_url.url if obj.book.cover_image_url else None
    
    def get_thumbnail_url(self, obj):
        return obj.book.thumbnail_url.url if obj.book.thumbnail_url else None
    
    class Meta:
        model = BookPopularity
        fields = [
            'book_id', 'title', 'subtitle', 'author_name', 'category_name',
            'price', 'short_description', 'cover_image_url', 'thumbnail_url',
            'rank', 'popularity_status', 'sales_count', 'view_count',
            'average_rating', 'month'
        ]


class RecommendedBookSerializer(serializers.ModelSerializer):
    """Serializer for recommended books."""
    recommended_book_id = serializers.CharField(source='recommended_book.id', read_only=True)
    title = serializers.CharField(source='recommended_book.title', read_only=True)
    subtitle = serializers.CharField(source='recommended_book.subtitle', read_only=True, allow_null=True)
    author_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='recommended_book.category.name', read_only=True, allow_null=True)
    price = serializers.DecimalField(source='recommended_book.price', max_digits=10, decimal_places=2, read_only=True)
    short_description = serializers.CharField(source='recommended_book.short_description', read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    def get_author_name(self, obj) -> str:
        return obj.recommended_book.author.user.get_full_name() or obj.recommended_book.author.user.username
    
    def get_cover_image_url(self, obj):
        return obj.recommended_book.cover_image_url.url if obj.recommended_book.cover_image_url else None
    
    def get_thumbnail_url(self, obj):
        return obj.recommended_book.thumbnail_url.url if obj.recommended_book.thumbnail_url else None
    
    class Meta:
        model = BookRecommendation
        fields = [
            'id', 'recommended_book_id', 'title', 'subtitle', 'author_name',
            'category_name', 'price', 'short_description', 'cover_image_url',
            'thumbnail_url', 'recommendation_type', 'score', 'reason'
        ]
