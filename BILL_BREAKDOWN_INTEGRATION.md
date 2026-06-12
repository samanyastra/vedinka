# Integration Example: Bill Breakdown + Transaction Handler

This file shows practical integration patterns for using BillBreakdownHandler
before TransactionHandler in subscription and order endpoints.

## Example 1: Subscription Verification Endpoint

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.finance.bill_breakdown_handler import BillBreakdownHandler
from apps.finance.transaction_handler import TransactionHandler
from apps.subscription.models import Subscription, SubscriptionType

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment_for_subscription(request):
    """
    Subscription payment verification flow:
    1. Calculate bill breakdown with charges
    2. Create transaction with final amount
    3. Verify payment
    4. Store breakdown in ledger
    """
    try:
        subscription_id = request.data.get('subscription_id')
        checkout_data = request.data.get('checkout_data')
        
        # Get subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        # Step 1: Calculate breakdown
        breakdown_handler = BillBreakdownHandler(
            user_id=request.user.id,
            subtotal=subscription.subscription_type.price,
            transaction_type="SUBSCRIPTION",
            reference_id=f"SUB_{subscription_id}"
        )
        
        breakdown = breakdown_handler.calculate_breakdown()
        
        # Step 2: Create transaction handler with final amount
        tx_handler = TransactionHandler(
            user_id=request.user.id,
            transaction_amount=breakdown_handler.final_amount,
            actual_amount=subscription.subscription_type.price
        )
        
        # Step 3: Verify payment
        if not tx_handler.verify_transaction(checkout_data):
            return Response(
                {'error': 'Payment verification failed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Step 4: Complete transaction
        tx_handler.complete_transaction()
        
        # Step 5: Save breakdown to ledger
        bill_ledger = breakdown_handler.save_bill_ledger()
        
        # Step 6: Create invoice dict for email
        invoice_dict = breakdown_handler.create_invoice_dict()
        invoice_dict.update({
            'product_name': subscription.subscription_type.name,
            'duration_days': subscription.subscription_type.duration_days,
            'valid_till': subscription.valid_till.isoformat(),
            'transaction_id': str(tx_handler.payment.id),
            'payment_method': tx_handler.gateway.upper(),
        })
        
        # Send confirmation email
        send_subscription_invoice_email(invoice_dict)
        
        return Response({
            'message': 'Payment verified successfully',
            'breakdown': breakdown,
            'bill_ledger_id': bill_ledger.id,
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
```

## Example 2: Cart Checkout Endpoint

```python
from apps.finance.bill_breakdown_handler import BillBreakdownHandler
from apps.finance.transaction_handler import TransactionHandler
from apps.finance.models import Cart, Order, OrderItem

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout_cart(request):
    """
    Cart checkout flow:
    1. Calculate cart subtotal
    2. Apply bill breakdown charges
    3. Create transaction with final amount
    4. Verify payment
    5. Create order items
    6. Generate invoice
    """
    try:
        checkout_data = request.data.get('checkout_data')
        
        # Get user's cart
        cart = Cart.objects.get(user=request.user.profile)
        
        # Calculate subtotal
        subtotal = sum(
            item.book.price * item.quantity 
            for item in cart.items.all()
        )
        
        if subtotal <= 0:
            return Response(
                {'error': 'Cart is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Step 1: Calculate breakdown with charges
        breakdown_handler = BillBreakdownHandler(
            user_id=request.user.id,
            subtotal=subtotal,
            transaction_type="ORDER",
            reference_id=f"CART_{cart.id}"
        )
        
        breakdown = breakdown_handler.calculate_breakdown()
        final_amount = breakdown_handler.final_amount
        
        # Step 2: Create transaction
        tx_handler = TransactionHandler(
            user_id=request.user.id,
            transaction_amount=final_amount,
            actual_amount=subtotal
        )
        
        # Step 3: Verify payment
        if not tx_handler.verify_transaction(checkout_data):
            return Response(
                {'error': 'Payment verification failed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Step 4: Complete transaction
        tx_handler.complete_transaction()
        
        # Step 5: Create order with items
        order = tx_handler.order
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                book=cart_item.book,
                price_at_purchase=cart_item.book.price,
                quantity=cart_item.quantity
            )
        
        # Step 6: Save breakdown
        bill_ledger = breakdown_handler.save_bill_ledger()
        
        # Step 7: Create invoice dict
        invoice_dict = breakdown_handler.create_invoice_dict()
        invoice_dict.update({
            'order_id': order.local_order_id,
            'items': [
                {
                    'title': item.book.title,
                    'price': float(item.price_at_purchase),
                    'quantity': item.quantity,
                }
                for item in order.items.all()
            ],
            'transaction_id': str(tx_handler.payment.id),
            'payment_method': tx_handler.gateway.upper(),
        })
        
        # Send order confirmation email
        send_order_invoice_email(invoice_dict)
        
        # Clear cart
        cart.items.all().delete()
        
        return Response({
            'message': 'Order placed successfully',
            'order_id': order.local_order_id,
            'final_amount': float(final_amount),
            'breakdown': breakdown,
        })
        
    except Cart.DoesNotExist:
        return Response(
            {'error': 'Cart not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
```

## Example 3: Admin Endpoint - View User Bills

```python
from apps.finance.models import BillLedger

@api_view(['GET'])
@permission_classes([IsSuperUserOrAdmin])
def get_user_bills(request, user_id):
    """
    Get all bill ledger entries for a user with breakdown details
    """
    try:
        ledger_entries = BillLedger.objects.filter(
            user_id=user_id
        ).order_by('-created_at')
        
        data = []
        for entry in ledger_entries:
            data.append({
                'id': entry.id,
                'transaction_type': entry.transaction_type,
                'reference_id': entry.reference_id,
                'subtotal': float(entry.subtotal),
                'total_charges': float(entry.total_charges),
                'final_amount': float(entry.final_amount),
                'breakdown': entry.breakdown_json,
                'created_at': entry.created_at.isoformat(),
            })
        
        return Response(data)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
```

## Key Integration Points

1. **Calculate Breakdown First** - Always create BillBreakdownHandler before TransactionHandler
2. **Use Final Amount** - Pass `breakdown_handler.final_amount` to TransactionHandler
3. **Store Audit Trail** - Save breakdown to BillLedger after payment success
4. **Generate Invoices** - Use `create_invoice_dict()` for email templates
5. **Error Handling** - Validate breakdown before processing transaction

## Email Template Usage

```python
# In template (subscription_invoice.html)
<tr>
    <td class="label">Subtotal:</td>
    <td>₹{{ subtotal }}</td>
</tr>
{% for charge in charges %}
<tr>
    <td class="label">{{ charge.name }}:</td>
    <td>{{ charge.calculated_amount }} ({{ charge.amount_type }})</td>
</tr>
{% endfor %}
<tr style="border-top: 2px solid #7A1354;">
    <td class="label"><strong>Total:</strong></td>
    <td><strong>₹{{ final_amount }}</strong></td>
</tr>
```

## Testing Breakdown Calculation

```python
# Manual test
from apps.finance.bill_breakdown_handler import BillBreakdownHandler

handler = BillBreakdownHandler(
    user_id=1,
    subtotal=1000,
    transaction_type="ORDER"
)

print(handler.get_breakdown_summary())

# Check ledger
from apps.finance.models import BillLedger
entry = BillLedger.objects.latest('created_at')
print(entry.breakdown_json)
```
