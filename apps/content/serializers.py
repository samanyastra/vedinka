"""
Serializers for content management (books, categories, etc).
"""
from rest_framework import serializers
from apps.content.models import Book, Category, Subcategory, Tag
from apps.common.models import Genre, Language
from typing import List, Dict, Any


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for book categories."""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'short_description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SubcategorySerializer(serializers.ModelSerializer):
    """Serializer for book subcategories."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Subcategory
        fields = ['id', 'category', 'category_name', 'name', 'short_description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for book tags."""
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'usage_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class LanguageSerializer(serializers.ModelSerializer):
    """Serializer for languages."""
    
    class Meta:
        model = Language
        fields = ['id', 'language_name', 'language_code', 'place_used']
        read_only_fields = ['id']


class GenreSerializer(serializers.ModelSerializer):
    """Serializer for genres."""
    
    class Meta:
        model = Genre
        fields = ['id', 'name', 'usage_count']
        read_only_fields = ['id', 'usage_count']


class BookListSerializer(serializers.ModelSerializer):
    """Serializer for book list view."""
    author_name = serializers.CharField(source='author.user.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    language_name = serializers.CharField(source='language.name', read_only=True)
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'subtitle', 'author', 'author_name', 'category', 'category_name',
            'language', 'language_name', 'short_description', 'price', 'cover_image_url',
            'thumbnail_url', 'purchase_count', 'is_checks_passed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'purchase_count', 'created_at', 'updated_at']


class BookDetailSerializer(serializers.ModelSerializer):
    """Serializer for book detail view."""
    author_name = serializers.CharField(source='author.user.get_full_name', read_only=True)
    author_email = serializers.CharField(source='author.user.email', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    language_name = serializers.CharField(source='language.name', read_only=True)
    tags = TagSerializer(source='tags_relation', many=True, read_only=True)
    genres = serializers.SerializerMethodField()
    
    def get_genres(self, obj) -> List[Dict[str, Any]]:
        """Get genres for the book."""
        genres = obj.genres_relation.all()
        return [{'id': str(g.genre.id), 'name': g.genre.name} for g in genres]
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'subtitle', 'author', 'author_name', 'author_email',
            'category', 'category_name', 'subcategory', 'subcategory_name',
            'language', 'language_name', 'short_description', 'full_description',
            'number_of_pages', 'price', 'cover_image_url', 'thumbnail_url',
            'sample_read_url', 'index_file_url', 'purchase_count', 'is_checks_passed',
            'tags', 'genres', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'purchase_count', 'created_at', 'updated_at'
        ]
