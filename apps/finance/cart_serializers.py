from rest_framework import serializers
from django.db.models import F, Sum, DecimalField
from apps.finance.models import Cart, CartItem
from apps.content.serializers import BookListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items with book details."""
    book = BookListSerializer(read_only=True)
    book_id = serializers.CharField(write_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'book', 'book_id', 'quantity', 'added_at']
        read_only_fields = ['id', 'added_at']


class CartSerializer(serializers.ModelSerializer):
    """Serializer for user cart with items."""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    
    def get_total_items(self, obj) -> int:
        return obj.items.aggregate(total=Sum('quantity'))['total'] or 0
    
    def get_total_price(self, obj) -> str:
        total = obj.items.aggregate(
            total=Sum(F('book__price') * F('quantity'), output_field=DecimalField())
        )['total'] or 0
        return str(total)
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_items', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
