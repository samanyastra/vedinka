"""Author-focused APIs for managing tags, genres, languages.
GET endpoints require authentication, POST endpoints require author/admin role.
"""
from django.db import models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.content.models import Tag
from apps.common.models import Genre, Language
from apps.users.models import BankDetail
from apps.content.author_serializers import BankDetailSerializer
from apps.content.serializers import TagSerializer, GenreSerializer, LanguageSerializer
from apps.auth.permissions import IsAuthorOrAdmin
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


# ============================================================================
# TAG ENDPOINTS
# ============================================================================

@extend_schema(
    operation_id='search_tags',
    summary='Search tags',
    description='Search tags by name with query parameter. Authenticated users only.',
    parameters=[
        OpenApiParameter(
            name='q',
            description='Search query for tag name',
            required=False,
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
        )
    ],
    responses={200: TagSerializer(many=True)},
    tags=['Author - Tags'],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_tags(request: Request) -> Response:
    """Search tags by name."""
    query = request.GET.get('q', '').strip()
    
    tags = Tag.objects.all()
    if query:
        tags = tags.filter(name__icontains=query)
    
    tags = tags.order_by('name')[:50]
    serializer = TagSerializer(tags, many=True)
    return Response(serializer.data)


@extend_schema(
    operation_id='create_tag',
    summary='Create tag',
    description='Create a new tag. Author/Admin only.',
    request=TagSerializer,
    responses={201: TagSerializer},
    tags=['Author - Tags'],
)
@api_view(['POST'])
@permission_classes([IsAuthorOrAdmin])
def create_tag(request: Request) -> Response:
    """Create a new tag."""
    serializer = TagSerializer(data=request.data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors, code=400)
    
    tag = serializer.save()
    return Response(TagSerializer(tag).data, status=status.HTTP_201_CREATED)


# ============================================================================
# GENRE ENDPOINTS
# ============================================================================

@extend_schema(
    operation_id='search_genres',
    summary='Search genres',
    description='Search genres by name with query parameter. Authenticated users only.',
    parameters=[
        OpenApiParameter(
            name='q',
            description='Search query for genre name',
            required=False,
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
        )
    ],
    responses={200: GenreSerializer(many=True)},
    tags=['Author - Genres'],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_genres(request: Request) -> Response:
    """Search genres by name."""
    query = request.GET.get('q', '').strip()
    
    genres = Genre.objects.all()
    if query:
        genres = genres.filter(name__icontains=query)
    
    genres = genres.order_by('name')[:50]
    serializer = GenreSerializer(genres, many=True)
    return Response(serializer.data)


@extend_schema(
    operation_id='create_genre',
    summary='Create genre',
    description='Create a new genre. Author/Admin only.',
    request=GenreSerializer,
    responses={201: GenreSerializer},
    tags=['Author - Genres'],
)
@api_view(['POST'])
@permission_classes([IsAuthorOrAdmin])
def create_genre(request: Request) -> Response:
    """Create a new genre."""
    serializer = GenreSerializer(data=request.data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors, code=400)
    
    genre = serializer.save()
    return Response(GenreSerializer(genre).data, status=status.HTTP_201_CREATED)


# ============================================================================
# LANGUAGE ENDPOINTS
# ============================================================================

@extend_schema(
    operation_id='search_languages',
    summary='Search languages',
    description='Search languages by name or code with query parameter. Authenticated users only.',
    parameters=[
        OpenApiParameter(
            name='q',
            description='Search query for language name or code',
            required=False,
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
        )
    ],
    responses={200: LanguageSerializer(many=True)},
    tags=['Author - Languages'],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_languages(request: Request) -> Response:
    """Search languages by name or code."""
    query = request.GET.get('q', '').strip()
    
    languages = Language.objects.all()
    if query:
        languages = languages.filter(
            models.Q(language_name__icontains=query) | models.Q(language_code__icontains=query)
        )
    
    languages = languages.order_by('language_name')[:50]
    serializer = LanguageSerializer(languages, many=True)
    return Response(serializer.data)


@extend_schema(
    operation_id='create_language',
    summary='Create language',
    description='Create a new language. Author/Admin only.',
    request=LanguageSerializer,
    responses={201: LanguageSerializer},
    tags=['Author - Languages'],
)
@api_view(['POST'])
@permission_classes([IsAuthorOrAdmin])
def create_language(request: Request) -> Response:
    """Create a new language."""
    serializer = LanguageSerializer(data=request.data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors, code=400)
    
    language = serializer.save()
    return Response(LanguageSerializer(language).data, status=status.HTTP_201_CREATED)


# ============================================================================
# BANK DETAIL ENDPOINTS
# ============================================================================

@extend_schema(
    operation_id='get_bank_details',
    summary='Get my bank details',
    description='Retrieve authenticated user\'s bank account details.',
    responses={200: BankDetailSerializer},
    tags=['Bank Details'],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bank_details(request: Request) -> Response:
    """Get authenticated user's bank details."""
    try:
        bank_detail = BankDetail.objects.get(author=request.user.profile)
        serializer = BankDetailSerializer(bank_detail)
        return Response(serializer.data)
    except BankDetail.DoesNotExist:
        raise ValidationError({'error': 'Bank details not found'}, code=404)
    except Exception as e:
        raise ValidationError({'error': str(e)}, code=400)

