"""
Shopping cart endpoints for authenticated users.
GET and POST endpoints require authentication.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.finance.models import Cart, CartItem
from apps.content.models import Book
from apps.finance.cart_serializers import CartSerializer, CartItemSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


# ============================================================================
# CART ENDPOINTS
# ============================================================================

@extend_schema(
    operation_id='get_user_cart',
    summary='Get user cart',
    description='Retrieve authenticated user\'s shopping cart with all items',
    responses={200: CartSerializer},
    tags=['Cart'],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_cart(request: Request) -> Response:
    """Get authenticated user's cart."""
    try:
        user_profile = request.user.profile
        cart, created = Cart.objects.get_or_create(user=user_profile)
        
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    except Exception as e:
        raise ValidationError({'error': str(e)}, code=400)


@extend_schema(
    operation_id='add_to_cart',
    summary='Add item to cart',
    description='Add a book to authenticated user\'s shopping cart',
    request={
        'type': 'object',
        'properties': {
            'book_id': {'type': 'string', 'format': 'uuid'},
            'quantity': {'type': 'integer', 'default': 1}
        },
        'required': ['book_id']
    },
    responses={201: CartItemSerializer},
    tags=['Cart'],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request: Request) -> Response:
    """Add a book to user's cart."""
    try:
        book_id = request.data.get('book_id')
        quantity = request.data.get('quantity', 1)
        
        if not book_id:
            raise ValidationError({'error': 'book_id is required'}, code=400)
        
        if quantity < 1:
            raise ValidationError({'error': 'Quantity must be at least 1'}, code=400)
        
        book = Book.objects.filter(id=book_id).first()
        if not book:
            raise ValidationError({'error': 'Book not found'}, code=404)
        
        user_profile = request.user.profile
        cart, _ = Cart.objects.get_or_create(user=user_profile)
        
        # Add or update cart item
        cart_item, created = CartItem.objects.update_or_create(
            cart=cart,
            book=book,
            defaults={'quantity': quantity}
        )
        
        serializer = CartItemSerializer(cart_item)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError({'error': str(e)}, code=400)


@extend_schema(
    operation_id='remove_from_cart',
    summary='Remove item from cart',
    description='Remove a book from authenticated user\'s shopping cart',
    parameters=[
        OpenApiParameter(
            name='book_id',
            description='Book ID to remove',
            required=True,
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.QUERY,
        )
    ],
    responses={200: {'type': 'object', 'properties': {'status': {'type': 'string'}}}},
    tags=['Cart'],
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request: Request) -> Response:
    """Remove a book from user's cart."""
    try:
        book_id = request.GET.get('book_id')
        
        if not book_id:
            raise ValidationError({'error': 'book_id is required'}, code=400)
        
        user_profile = request.user.profile
        cart = Cart.objects.filter(user=user_profile).first()
        
        if not cart:
            raise ValidationError({'error': 'Cart not found'}, code=404)
        
        cart_item = CartItem.objects.filter(cart=cart, book_id=book_id).first()
        if not cart_item:
            raise ValidationError({'error': 'Item not found in cart'}, code=404)
        
        cart_item.delete()
        
        return Response({
            'status': 'success',
            'message': 'Item removed from cart'
        })
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError({'error': str(e)}, code=400)


@extend_schema(
    operation_id='clear_cart',
    summary='Clear user cart',
    description='Remove all items from authenticated user\'s shopping cart',
    responses={200: {'type': 'object', 'properties': {'status': {'type': 'string'}}}},
    tags=['Cart'],
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_cart(request: Request) -> Response:
    """Clear all items from user's cart."""
    try:
        user_profile = request.user.profile
        cart = Cart.objects.filter(user=user_profile).first()
        
        if not cart:
            raise ValidationError({'error': 'Cart not found'}, code=404)
        
        cart.items.all().delete()
        
        return Response({
            'status': 'success',
            'message': 'Cart cleared successfully'
        })
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError({'error': str(e)}, code=400)
