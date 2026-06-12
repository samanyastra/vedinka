"""
Book showcase APIs - Featured, Popular, and Recommended books.
GET endpoints are public (no authentication required), POST endpoints are admin only.
Uses existing models: Book (is_featured flag), BookPopularity, BookRecommendation.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework import status
from datetime import date

from apps.content.models import Book, BookPopularity, BookRecommendation
from apps.content.book_showcase_serializers import (
    FeaturedBookSerializer,
    PopularBookSerializer,
    RecommendedBookSerializer,
)
from apps.auth.permissions import IsSuperUserOrAdmin
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.pagination import PageNumberPagination


# ============================================================================
# FEATURED BOOKS ENDPOINTS
# ============================================================================

@extend_schema(
    operation_id='get_featured_books',
    summary='Get featured books',
    description='Get all featured books with pagination. Public access.',
    responses={200: FeaturedBookSerializer(many=True)},
    tags=['Books - Showcase'],
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_featured_books(request: Request) -> Response:
    """Get all featured books."""
    try:
        featured_books = Book.objects.filter(is_featured=True).prefetch_related('tags_relation', 'genres_relation')
        
        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 30
        paginated_books = paginator.paginate_queryset(featured_books, request)
        
        serializer = FeaturedBookSerializer(paginated_books, many=True)
        return paginator.get_paginated_response(serializer.data)
    except Exception as e:
        raise ValidationError({'error': str(e)}, code=400)


@extend_schema(
    operation_id='toggle_featured_book',
    summary='Toggle featured book status',
    description='Toggle a book as featured or unfeatured. Admin only.',
    parameters=[
        OpenApiParameter(
            name='book_id',
            description='Book ID to toggle',
            required=True,
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.QUERY,
        )
    ],
    responses={200: {'type': 'object', 'properties': {'status': {'type': 'string'}}}},
    tags=['Books - Showcase'],
)
@api_view(['POST'])
@permission_classes([IsSuperUserOrAdmin])
def toggle_featured_book(request: Request) -> Response:
    """Toggle a book as featured or unfeatured."""
    try:
        book_id = request.GET.get('book_id')
        
        if not book_id:
            raise ValidationError({'error': 'book_id is required'}, code=400)
        
        book = Book.objects.filter(id=book_id).first()
        if not book:
            raise ValidationError({'error': 'Book not found'}, code=404)
        
        book.is_featured = not book.is_featured
        book.save()
        
        return Response({
            'status': 'success',
            'book_id': str(book.id),
            'is_featured': book.is_featured
        })
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError({'error': str(e)}, code=400)


# ============================================================================
# POPULAR BOOKS ENDPOINTS
# ============================================================================

@extend_schema(
    operation_id='get_popular_books',
    summary='Get popular books',
    description='Get books sorted by popularity from current month. Public access.',
    responses={200: PopularBookSerializer(many=True)},
    tags=['Books - Showcase'],
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_popular_books(request: Request) -> Response:
    """Get popular books from current month."""
    try:
        today = date.today()
        first_day_of_month = today.replace(day=1)
        
        popular_books = BookPopularity.objects.filter(
            month=first_day_of_month
        ).select_related('book').order_by('rank')
        
        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 30
        paginated_books = paginator.paginate_queryset(popular_books, request)
        
        serializer = PopularBookSerializer(paginated_books, many=True)
        return paginator.get_paginated_response(serializer.data)
    except Exception as e:
        raise ValidationError({'error': str(e)}, code=400)


# ============================================================================
# RECOMMENDED BOOKS ENDPOINTS
# ============================================================================

@extend_schema(
    operation_id='get_recommended_books',
    summary='Get recommended books',
    description='Get recommended books. Can filter by book_id and recommendation_type. Public access.',
    parameters=[
        OpenApiParameter(
            name='book_id',
            description='Filter by book ID',
            required=False,
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name='recommendation_type',
            description='Filter by recommendation type (similar, author, genre, trending, curated, seasonal, custom)',
            required=False,
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
        )
    ],
    responses={200: RecommendedBookSerializer(many=True)},
    tags=['Books - Showcase'],
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_recommended_books(request: Request) -> Response:
    """Get recommended books with optional filtering."""
    try:
        book_id = request.GET.get('book_id')
        recommendation_type = request.GET.get('recommendation_type')
        
        recommendations = BookRecommendation.objects.filter(
            is_active=True
        ).select_related('book', 'recommended_book').order_by('-score', 'display_order')
        
        if book_id:
            recommendations = recommendations.filter(book_id=book_id)
        
        if recommendation_type:
            recommendations = recommendations.filter(recommendation_type=recommendation_type)
        
        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 30
        paginated_recommendations = paginator.paginate_queryset(recommendations, request)
        
        serializer = RecommendedBookSerializer(paginated_recommendations, many=True)
        return paginator.get_paginated_response(serializer.data)
    except Exception as e:
        raise ValidationError({'error': str(e)}, code=400)


@extend_schema(
    operation_id='add_recommended_book',
    summary='Add recommended book',
    description='Add a book recommendation. Admin only.',
    request={
        'type': 'object',
        'properties': {
            'book_id': {'type': 'string'},
            'recommended_book_id': {'type': 'string'},
            'recommendation_type': {'type': 'string'},
            'score': {'type': 'number'},
            'reason': {'type': 'string'},
        }
    },
    responses={201: RecommendedBookSerializer},
    tags=['Books - Showcase'],
)
@api_view(['POST'])
@permission_classes([IsSuperUserOrAdmin])
def add_recommended_book(request: Request) -> Response:
    """Add a book recommendation."""
    try:
        book_id = request.data.get('book_id')
        recommended_book_id = request.data.get('recommended_book_id')
        recommendation_type = request.data.get('recommendation_type', 'similar')
        score = request.data.get('score', 0.5)
        reason = request.data.get('reason', '')
        
        if not book_id or not recommended_book_id:
            raise ValidationError({'error': 'book_id and recommended_book_id are required'}, code=400)
        
        book = Book.objects.filter(id=book_id).first()
        recommended_book = Book.objects.filter(id=recommended_book_id).first()
        
        if not book or not recommended_book:
            raise ValidationError({'error': 'One or both books not found'}, code=404)
        
        recommendation, created = BookRecommendation.objects.update_or_create(
            book=book,
            recommended_book=recommended_book,
            defaults={
                'recommendation_type': recommendation_type,
                'score': score,
                'reason': reason,
                'is_active': True
            }
        )
        
        serializer = RecommendedBookSerializer(recommendation)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError({'error': str(e)}, code=400)
