"""
USER SUBSCRIPTION VIEWS - REFACTORING WITH TRANSACTIONHANDLER
==============================================================

OVERVIEW:
=========

The user_subscription_views.py has been refactored to use the TransactionHandler
from the finance app instead of duplicating payment processing logic.

This eliminates code duplication and leverages the existing, battle-tested
payment infrastructure already in place.


BEFORE (Code Duplication):
==========================

create_subscription_order():
  • Manually created Razorpay client
  • Manually called client.order.create()
  • Manually handled order creation
  • No integration with finance app

verify_payment():
  • Manually verified HMAC signature
  • Manually created Order and Payment records
  • Duplicated payment verification logic
  • No use of existing TransactionHandler

generate_invoice():
  • Standalone invoice generation
  • No connection to finance app records


AFTER (Using TransactionHandler):
==================================

create_subscription_order():
  ✓ Uses TransactionHandler for order creation
  ✓ Automatically creates Order and Payment records in finance app
  ✓ Handles Razorpay client initialization
  ✓ Integrated with finance infrastructure

verify_payment():
  ✓ Uses TransactionHandler.verify_transaction()
  ✓ Leverages built-in signature verification
  ✓ Automatically updates Order and Payment records
  ✓ Consistent with finance app patterns

generate_invoice():
  ✓ Uses helper function _send_invoice_email()
  ✓ Reusable across both verify_payment and generate_invoice
  ✓ DRY principle applied


BENEFITS:
=========

1. CODE REUSABILITY
   • No duplication of payment logic
   • Single source of truth for payment handling
   • Easier to maintain and update

2. CONSISTENCY
   • All payments handled through TransactionHandler
   • Unified Order and Payment record creation
   • Consistent status management

3. INTEGRATION
   • Finance app records automatically created
   • Payment tracking across the system
   • Better audit trails

4. MAINTAINABILITY
   • Changes to payment logic only in one place
   • Easier to add new payment gateways
   • Reduced bug surface area

5. SCALABILITY
   • Supports multiple payment gateways
   • Gateway-agnostic design
   • Easy to extend


REFACTORING DETAILS:
====================

1. IMPORTS CHANGED:
   
   Before:
     import razorpay
     import hmac
     import hashlib
     from django.conf import settings
   
   After:
     from apps.finance.transaction_handler import TransactionHandler

2. create_subscription_order() REFACTORED:
   
   Before:
     • Manually created Razorpay client
     • Called client.order.create() directly
     • Only created SubscriptionOrder record
   
   After:
     • Uses TransactionHandler(user_id, transaction_amount)
     • Calls handler.create_remote_transaction()
     • Automatically creates Order and Payment records
     • Links SubscriptionOrder to Payment record

3. verify_payment() REFACTORED:
   
   Before:
     • Manual HMAC signature verification
     • Manual Order and Payment creation
     • Duplicated logic from finance app
   
   After:
     • Uses handler.verify_transaction(checkout_data)
     • Uses handler.complete_transaction()
     • Automatic record updates
     • Consistent with finance app

4. generate_invoice() REFACTORED:
   
   Before:
     • Inline invoice generation code
     • Duplicated in verify_payment()
   
   After:
     • Uses helper function _send_invoice_email()
     • Reusable across endpoints
     • DRY principle applied


CODE COMPARISON:
================

BEFORE - create_subscription_order():
```python
import razorpay
client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)
razorpay_order = client.order.create({
    'amount': int(subscription_type.cost * 100),
    'currency': subscription_type.currency,
    'receipt': f'order_{user_profile.id}_{subscription_type.id}',
})
order = SubscriptionOrder.objects.create(...)
```

AFTER - create_subscription_order():
```python
handler = TransactionHandler(
    user_id=request.user.id,
    transaction_amount=float(subscription_type.cost)
)
remote_order = handler.create_remote_transaction()
order = SubscriptionOrder.objects.create(
    razorpay_order_id=remote_order['id'],
    ...
)
```

Benefits:
  ✓ Cleaner code
  ✓ Automatic Order and Payment creation
  ✓ Consistent with finance app
  ✓ Easier to test


BEFORE - verify_payment():
```python
signature_payload = f"{data['razorpay_order_id']}|{data['razorpay_payment_id']}"
expected_signature = hmac.new(
    settings.RAZORPAY_KEY_SECRET.encode(),
    signature_payload.encode(),
    hashlib.sha256
).hexdigest()
if expected_signature != data['razorpay_signature']:
    raise ValidationError(...)
```

AFTER - verify_payment():
```python
handler = TransactionHandler(
    user_id=request.user.id,
    transaction_amount=float(order.amount)
)
if not handler.verify_transaction(checkout_data):
    raise ValidationError(...)
payment = handler.complete_transaction()
```

Benefits:
  ✓ No manual signature verification
  ✓ Automatic Payment record updates
  ✓ Consistent error handling
  ✓ Reusable verification logic


BEFORE - Invoice Email (duplicated):
```python
# In verify_payment()
send_email.delay(
    'subscription_confirmation',
    'Subscription Activated',
    order.user.user.email,
    subscription_name=order.subscription_type.name,
    valid_till=valid_till.strftime('%Y-%m-%d'),
)

# In generate_invoice()
html_message = render_to_string(...)
send_email.delay(
    'subscription_invoice',
    f'Invoice for {order.subscription_type.name} Subscription',
    order.user.user.email,
    html_message=html_message,
)
```

AFTER - Invoice Email (DRY):
```python
def _send_invoice_email(order, valid_till):
    # Shared logic
    html_message = render_to_string(...)
    send_email.delay(...)

# Used in both verify_payment() and generate_invoice()
_send_invoice_email(order, valid_till)
```

Benefits:
  ✓ No code duplication
  ✓ Single source of truth
  ✓ Easier to maintain
  ✓ Consistent email format


TRANSACTIONHANDLER FEATURES USED:
==================================

1. __init__(user_id, transaction_amount)
   • Initializes handler
   • Creates local Order and Payment records
   • Prepares order payload

2. create_remote_transaction()
   • Creates order on Razorpay
   • Stores gateway reference
   • Returns remote order object

3. verify_transaction(checkout_data)
   • Verifies payment signature
   • Validates checkout data
   • Returns boolean

4. complete_transaction()
   • Marks payment as SUCCESS
   • Updates Order and Payment records
   • Returns updated Payment object


INTEGRATION WITH FINANCE APP:
=============================

Now subscription payments are tracked in the finance app:

Order Model:
  • local_order_id: Unique local identifier
  • client_order_id: Razorpay order ID
  • user: UserProfile
  • transaction_status: PENDING → SUCCESS
  • amount: Subscription cost
  • order_date: Date of order

Payment Model:
  • order: Link to Order
  • gateway: "razorpay"
  • gateway_payment_id: Razorpay payment ID
  • gateway_order_id: Razorpay order ID
  • status: PENDING → SUCCESS
  • amount: Subscription cost
  • raw_response: Full Razorpay response


BENEFITS OF INTEGRATION:
========================

1. UNIFIED PAYMENT TRACKING
   • All payments in one place
   • Easy to generate reports
   • Better financial visibility

2. AUDIT TRAIL
   • Complete payment history
   • Raw gateway responses stored
   • Easy to debug issues

3. EXTENSIBILITY
   • Easy to add new payment gateways
   • Consistent interface
   • Reusable across apps

4. ANALYTICS
   • Payment metrics
   • Revenue tracking
   • User payment patterns


MIGRATION NOTES:
================

If you have existing SubscriptionOrder records:

1. They won't have corresponding Order/Payment records
2. You can create them retroactively if needed
3. New orders will automatically have both

To link existing orders:
```python
from apps.finance.models import Order, Payment
from apps.common.models import TransactionStatus

for sub_order in SubscriptionOrder.objects.filter(payment__isnull=True):
    pending_status, _ = TransactionStatus.objects.get_or_create(name="PENDING")
    
    order = Order.objects.create(
        local_order_id=str(sub_order.id),
        user=sub_order.user,
        transaction_status=pending_status,
        amount=sub_order.amount,
        order_date=sub_order.created_at.date(),
        client_order_id=sub_order.razorpay_order_id,
    )
    
    payment = Payment.objects.create(
        order=order,
        gateway="razorpay",
        gateway_payment_id=sub_order.razorpay_payment_id or "",
        gateway_order_id=sub_order.razorpay_order_id,
        status=sub_order.payment_status.upper(),
        amount=sub_order.amount,
    )
```


TESTING:
========

The refactored code maintains the same API:

1. create_subscription_order()
   • Input: subscription_type_id
   • Output: SubscriptionOrder with razorpay_order_id
   • No change to endpoint behavior

2. verify_payment()
   • Input: razorpay_order_id, razorpay_payment_id, razorpay_signature
   • Output: Success response with subscription activated
   • No change to endpoint behavior

3. generate_invoice()
   • Input: order_id
   • Output: Invoice sent to email
   • No change to endpoint behavior


FUTURE IMPROVEMENTS:
====================

1. Add support for other payment gateways
   • Stripe, PayPal, etc.
   • TransactionHandler already supports this
   • Just pass different client

2. Add payment retry logic
   • Automatic retry on failure
   • Exponential backoff
   • Notification to user

3. Add subscription renewal
   • Automatic renewal on expiry
   • Recurring payment handling
   • Renewal reminders

4. Add payment analytics
   • Revenue reports
   • Payment success rates
   • User payment patterns


SUMMARY:
========

✓ Refactored to use TransactionHandler
✓ Eliminated code duplication
✓ Integrated with finance app
✓ Improved maintainability
✓ Better code organization
✓ Consistent payment handling
✓ Easier to extend and test
✓ Unified payment tracking

The refactoring maintains backward compatibility while improving code quality
and leveraging existing infrastructure.
"""
