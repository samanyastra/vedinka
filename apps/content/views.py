"""
Views for content management (books, categories, etc).
"""
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from apps.content.models import Book
from apps.content.serializers import BookListSerializer, BookDetailSerializer


class BookViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for books - currently supports only GET requests.
    
    POST, PUT, PATCH, DELETE methods will raise NotImplementedError.
    These will be implemented later.
    
    Supports filtering by:
    - price_min, price_max: Filter by price range
    - category: Filter by category ID
    - language: Filter by language ID
    - tags: Filter by tag IDs (comma-separated)
    - genres: Filter by genre IDs (comma-separated)
    - search: Search by title, subtitle, or author name
    """
    queryset = Book.objects.filter(is_checks_passed=True).select_related(
        'author', 'category', 'subcategory', 'language'
    ).prefetch_related('tags_relation', 'genres_relation')
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'language']
    search_fields = ['title', 'subtitle', 'author__user__first_name', 'author__user__last_name']
    ordering_fields = ['price', 'created_at', 'purchase_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return BookDetailSerializer
        return BookListSerializer
    
    def get_queryset(self):
        """Apply custom filters for price and tags/genres."""
        queryset = super().get_queryset()
        
        # Price range filtering
        price_min = self.request.query_params.get('price_min')
        price_max = self.request.query_params.get('price_max')
        
        if price_min:
            try:
                queryset = queryset.filter(price__gte=float(price_min))
            except (ValueError, TypeError):
                pass
        
        if price_max:
            try:
                queryset = queryset.filter(price__lte=float(price_max))
            except (ValueError, TypeError):
                pass
        
        # Tags filtering (comma-separated tag IDs)
        tags = self.request.query_params.get('tags')
        if tags:
            tag_ids = [t.strip() for t in tags.split(',') if t.strip()]
            if tag_ids:
                queryset = queryset.filter(tags_relation__tag_id__in=tag_ids).distinct()
        
        # Genres filtering (comma-separated genre IDs)
        genres = self.request.query_params.get('genres')
        if genres:
            genre_ids = [g.strip() for g in genres.split(',') if g.strip()]
            if genre_ids:
                queryset = queryset.filter(genres_relation__genre_id__in=genre_ids).distinct()
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """POST method not implemented yet."""
        raise NotImplementedError("Book creation is not yet implemented. Coming soon!")
    
    def update(self, request, *args, **kwargs):
        """PUT method not implemented yet."""
        raise NotImplementedError("Book update is not yet implemented. Coming soon!")
    
    def partial_update(self, request, *args, **kwargs):
        """PATCH method not implemented yet."""
        raise NotImplementedError("Book partial update is not yet implemented. Coming soon!")
    
    def destroy(self, request, *args, **kwargs):
        """DELETE method not implemented yet."""
        raise NotImplementedError("Book deletion is not yet implemented. Coming soon!")
    
    @extend_schema(
        operation_id='list_books',
        summary='List all books',
        description='Get all published books with pagination support',
        tags=['Books'],
    )
    def list(self, request, *args, **kwargs):
        """List all published books."""
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        operation_id='retrieve_book',
        summary='Get book details',
        description='Get detailed information about a specific book',
        tags=['Books'],
    )
    def retrieve(self, request, *args, **kwargs):
        """Get detailed information about a specific book."""
        return super().retrieve(request, *args, **kwargs)
