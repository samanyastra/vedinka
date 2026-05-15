# TransactionHandler

A central, gateway-agnostic utility class for handling payment transactions with support for multiple payment processors (Razorpay, Stripe, etc.). Manages the complete lifecycle of transactions: local order creation, remote gateway integration, payment verification, and order completion.

## Overview

`TransactionHandler` streamlines payment processing by:
- Creating local `Order` and `Payment` records in the database.
- Coordinating with payment gateway clients to create remote orders.
- Managing payment verification and transaction completion.
- Supporting multiple payment gateways through a flexible client injection pattern.
- Using Django's `get_or_create` for idempotent status management.

## Installation

Located at: `apps/finance/transaction_handler.py`

Import:
```python
from apps.finance.transaction_handler import TransactionHandler
```

## Dependencies

- Django models: `Order`, `Payment` (from `apps.finance.models`)
- Status model: `TransactionStatus` (from `apps.common.models`)
- Utilities: `get_object_or_none`, `create_rand_string` (from `apps.common.utils`)
- User model: Retrieved via `django.contrib.auth.get_user_model()`

## Configuration

Configure your payment gateway client in Django settings:

```python
# settings.py

# Razorpay example
import razorpay

RAZ_CLIENT = razorpay.Client(auth=("your-key-id", "your-secret-key"))
RAZORPAY_KEY = "your-public-key"

# Optional
COMPANY_NAME = "Samanyastra"  # Used in prefill information
```

## Usage

### Basic Initialization

```python
from apps.finance.transaction_handler import TransactionHandler

# Create a handler with a user and transaction amount
handler = TransactionHandler(
    user_id="user-uuid-here",
    transaction_amount=500.00  # in INR
)
```

### With Custom Gateway Client

```python
import razorpay

custom_client = razorpay.Client(auth=("key", "secret"))

handler = TransactionHandler(
    user_id="user-uuid-here",
    transaction_amount=500.00,
    client=custom_client,
    client_public_key="your-public-key",
    gateway="razorpay"
)
```

### Complete Payment Flow

#### 1. Initialize and Get Prefill Data

```python
handler = TransactionHandler(
    user_id=user_id,
    transaction_amount=500.00
)

# Get data to pass to frontend checkout form
prefill_data = handler.make_user_prefill_information()
# Returns:
# {
#     "key": "razorpay-public-key",
#     "prefill": {
#         "name": "John Doe",
#         "email": "john@example.com",
#         "contact": "+919876543210"
#     },
#     "amount": 50000,  # in paise
#     "currency": "INR",
#     "name": "Samanyastra",
#     "order_id": "order-gateway-id",
#     "config": {...},
#     "transaction_id": "payment-uuid"
# }
```

#### 2. Verify Payment (After Frontend Checkout)

```python
checkout_data = {
    "razorpay_order_id": "order_9A33XWu170gUtm",
    "razorpay_payment_id": "pay_9A33XWu170gUtm",
    "razorpay_signature": "9ef4dffbfd84f1318f6739a3ce19f9d85851857ae648f114332d8401e0949a3d"
}

try:
    is_valid = handler.verify_transaction(checkout_data)
    if is_valid:
        payment = handler.complete_transaction()
        print(f"Payment completed: {payment.id}")
except ValidationError as e:
    print(f"Invalid transaction: {e}")
```

#### 3. Complete Transaction

```python
payment = handler.complete_transaction()
# Updates:
# - Payment.status = "SUCCESS"
# - Payment.gateway_payment_id
# - Payment.gateway_order_id
# - Order.transaction_status = SUCCESS (via get_or_create)
# - Order.client_order_id
```

## API Reference

### `__init__`

Initializes the transaction handler and prepares local records.

**Parameters:**
- `user_id` (UUID): ID of the user making the payment.
- `transaction_amount` (float): Amount in INR.
- `actual_amount` (float, optional): Actual charged amount if different. Defaults to `transaction_amount`.
- `payment` (Payment, optional): Existing Payment record. If None, a new one is created.
- `client` (optional, keyword-only): Payment gateway client instance. Falls back to `settings.RAZ_CLIENT`.
- `client_public_key` (str, optional, keyword-only): Gateway public key. Falls back to `settings.RAZORPAY_KEY`.
- `gateway` (str, optional, keyword-only): Gateway name (default: `"razorpay"`).

**Raises:**
- `ValidationError`: If the provided user_id is invalid.

**Side Effects:**
- Creates `Order` and `Payment` records in the database.
- Prepares internal order payload for the gateway.

---

### `make_order_payload()`

Prepares the order payload for remote gateway submission.

**Returns:** Dictionary with `amount` (in paise), `currency`, and `receipt`.

```python
payload = handler.make_order_payload()
# {
#     "amount": 50000,      # INR 500 converted to paise
#     "currency": "INR",
#     "receipt": "order-local-id"
# }
```

---

### `create_remote_transaction()`

Creates an order on the payment gateway and stores the gateway reference locally.

**Returns:** Remote order object from the gateway.

**Raises:**
- `ValidationError`: If local order is not prepared.
- `RuntimeError`: If gateway client is not configured.
- `Exception`: If gateway API call fails.

**Side Effects:**
- Updates `Order.client_order_id` with the gateway order ID.
- Updates `Payment.gateway_order_id` with the gateway order ID.
- Stores raw gateway response in `Payment.raw_response`.

```python
remote_order = handler.create_remote_transaction()
print(remote_order['id'])  # Gateway order ID
```

---

### `make_user_prefill_information()`

Generates prefill data for the frontend checkout form. Automatically calls `create_remote_transaction()` if not already done.

**Returns:** Dictionary with checkout prefill information.

```python
prefill = handler.make_user_prefill_information()
# Pass this to your frontend to render the checkout form
```

**Data Structure:**
```python
{
    "key": "razorpay-public-key",
    "prefill": {
        "name": "John Doe",
        "email": "john@example.com",
        "contact": "+919876543210"
    },
    "amount": 50000,
    "currency": "INR",
    "name": "Samanyastra",
    "order_id": "gateway-order-id",
    "config": {...},
    "transaction_id": "local-payment-uuid"
}
```

---

### `verify_transaction(checkout_data)`

Verifies the payment signature received from the frontend after checkout.

**Parameters:**
- `checkout_data` (dict): Data from frontend containing:
  - `razorpay_order_id`
  - `razorpay_payment_id`
  - `razorpay_signature`

**Returns:** Boolean indicating if the signature is valid.

**Raises:**
- `ValidationError`: If required keys are missing from `checkout_data`.
- `RuntimeError`: If gateway client doesn't support signature verification.

```python
try:
    is_valid = handler.verify_transaction(checkout_data)
except ValidationError:
    # Incomplete or malformed data
    return error_response()
```

---

### `complete_transaction()`

Marks the payment and order as completed. Must be called **after** `verify_transaction()` succeeds.

**Returns:** Updated `Payment` object.

**Side Effects:**
- Updates `Payment.status` to `"SUCCESS"`.
- Updates `Payment.gateway_payment_id` and `gateway_order_id`.
- Merges `checkout_data` into `Payment.raw_response`.
- Updates `Order.transaction_status` to `SUCCESS` (created via `get_or_create`).
- Saves all changes to database.

```python
payment = handler.complete_transaction()
print(f"Transaction complete: {payment.id}")
```

---

### `inr_to_paise(value)`

Converts amount from INR to paise (1 INR = 100 paise).

**Parameters:**
- `value` (float): Amount in INR.

**Returns:** Integer amount in paise.

```python
paise = handler.inr_to_paise(500)  # 50000
```

---

### `config` (property)

Returns the payment gateway configuration object.

**Returns:** Dictionary with display preferences (e.g., hidden payment methods).

```python
config = handler.config
# {
#     "display": {
#         "hide": [{"method": "upi", "flows": ["qr"]}],
#         "preferences": {"show_default_blocks": True}
#     }
# }
```

## Database Models

### Order
- `local_order_id`: Unique identifier for local tracking.
- `client_order_id`: Gateway-assigned order ID.
- `user`: ForeignKey to UserProfile.
- `transaction_status`: ForeignKey to TransactionStatus.
- `amount`: Transaction amount in INR.
- `order_date`: Date of the order.

### Payment
- `order`: ForeignKey to Order.
- `gateway`: Payment gateway name (e.g., "razorpay").
- `gateway_payment_id`: Payment ID from gateway.
- `gateway_order_id`: Order ID from gateway.
- `status`: Current payment status.
- `amount`: Transaction amount.
- `raw_response`: JSON field storing full gateway response.

### TransactionStatus
- `name`: Status name (e.g., "PENDING", "SUCCESS", "FAILED").
- Uses `get_or_create` to ensure idempotent status management.

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `ValidationError: Invalid user id` | User doesn't exist | Verify user_id is correct |
| `RuntimeError: Gateway client not configured` | `client` and `settings.RAZ_CLIENT` both None | Provide client or set `RAZ_CLIENT` in settings |
| `ValidationError: Invalid or incomplete checkout data` | Missing required keys in checkout_data | Ensure `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature` are present |
| `RuntimeError: Gateway client does not support signature verification` | Client missing `utility.verify_payment_signature` | Ensure proper Razorpay client is configured |

## Example: Complete View Usage

```python
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.finance.transaction_handler import TransactionHandler

class CheckoutView(APIView):
    def post(self, request):
        user_id = request.user.profile.user.id
        amount = request.data.get('amount')
        
        try:
            handler = TransactionHandler(
                user_id=user_id,
                transaction_amount=amount
            )
            prefill = handler.make_user_prefill_information()
            return Response(prefill)
        except Exception as e:
            return Response({'error': str(e)}, status=400)


class VerifyPaymentView(APIView):
    def post(self, request):
        user_id = request.user.profile.user.id
        checkout_data = request.data
        
        try:
            handler = TransactionHandler(
                user_id=user_id,
                transaction_amount=checkout_data.get('amount')
            )
            if handler.verify_transaction(checkout_data):
                payment = handler.complete_transaction()
                return Response({
                    'status': 'success',
                    'payment_id': str(payment.id)
                })
            else:
                return Response({'status': 'failed'}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
```

## Status Management

The handler uses Django's `get_or_create()` for idempotent status management:

```python
pending_status, _ = TransactionStatus.objects.get_or_create(name="PENDING")
complete_status, _ = TransactionStatus.objects.get_or_create(name="SUCCESS")
```

This ensures:
- Statuses are created automatically if missing.
- Multiple calls don't create duplicates.
- No race conditions in concurrent environments.

## Notes

- Amounts are stored in **INR** in the handler and converted to **paise** for the gateway.
- User's phone number is retrieved from `UserProfile.phone_number`.
- User's name is constructed from `User.first_name` and `User.last_name`.
- The `config` property can be customized for different payment methods.
- The handler is gateway-agnostic; provide any compatible client.

## Security Considerations

- Always verify signatures via `verify_transaction()` before marking payments complete.
- Store `raw_response` for audit trails and debugging.
- Use `HTTPS` in production for all payment-related endpoints.
- Never expose gateway secret keys in the frontend.
