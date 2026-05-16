"""
INVOICE TEMPLATE - INTEGRATION GUIDE
====================================

COMPLETE WORKFLOW EXAMPLE:
==========================

1. USER INITIATES PURCHASE
   └─ POST /api/users/my-subscriptions/create-order/
      └─ Request: { "subscription_type_id": "uuid" }
      └─ Response: { "razorpay_order_id": "order_123..." }

2. FRONTEND INITIALIZES RAZORPAY
   └─ User completes payment in Razorpay modal

3. PAYMENT VERIFICATION
   └─ POST /api/users/my-subscriptions/verify-payment/
      └─ Request: {
           "razorpay_order_id": "order_123...",
           "razorpay_payment_id": "pay_456...",
           "razorpay_signature": "sig_789..."
         }
      └─ Backend Actions:
         ├─ Verify signature
         ├─ Update order status to 'completed'
         ├─ Create UserSubscription
         └─ Send invoice email (uses template)

4. INVOICE EMAIL SENT
   └─ Template: subscription_invoice.html
   └─ Context: All invoice details
   └─ Recipient: User's email


BACKEND IMPLEMENTATION:
=======================

File: apps/users/user_subscription_views.py

Function: verify_payment()

```python
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@document_api_view(...)
def verify_payment(request: Request) -> Response:
    # ... validation code ...
    
    # Create subscription
    valid_till = datetime.now() + timedelta(
        days=order.subscription_type.duration_in_days
    )
    subscription = UserSubscription.objects.create(
        user=order.user,
        subscription_type=order.subscription_type,
        valid_till=valid_till
    )
    
    # Prepare invoice context
    from decimal import Decimal
    platform_charges = order.amount * Decimal('0.02')
    total_amount = order.amount + platform_charges
    
    invoice_context = {
        'invoice_id': str(order.id)[:8].upper(),
        'invoice_date': order.created_at.strftime('%d %b, %Y'),
        'customer_name': order.user.user.get_full_name() or order.user.user.username,
        'customer_email': order.user.user.email,
        'product_name': order.subscription_type.name,
        'product_amount': f"{order.amount:.2f}",
        'duration_days': order.subscription_type.duration_in_days,
        'platform_charges': f"{platform_charges:.2f}",
        'total_amount': f"{total_amount:.2f}",
        'payment_method': 'Razorpay',
        'transaction_id': order.razorpay_payment_id,
        'valid_till': valid_till.strftime('%d %b, %Y'),
    }
    
    # Render template
    from django.template.loader import render_to_string
    html_message = render_to_string(
        'subscription_invoice.html',
        invoice_context
    )
    
    # Send email
    from apps.messaging.smtp import send_email
    send_email.delay(
        'subscription_confirmation',
        f'Subscription Activated - {order.subscription_type.name}',
        order.user.user.email,
        html_message=html_message,
    )
    
    return Response({
        "status": True,
        "message": "Payment verified and subscription activated"
    })
```


GENERATE INVOICE ON DEMAND:
===========================

Function: generate_invoice()

```python
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@document_api_view(...)
def generate_invoice(request: Request) -> Response:
    order_id = request.GET.get('order_id')
    order = get_object_or_none(SubscriptionOrder, id=order_id)
    
    if order.user != request.user.profile:
        raise ValidationError({"error": "Unauthorized"}, code=403)
    
    # Calculate charges
    from decimal import Decimal
    platform_charges = order.amount * Decimal('0.02')
    total_amount = order.amount + platform_charges
    
    # Get subscription for valid_till
    subscription = UserSubscription.objects.filter(
        user=order.user,
        subscription_type=order.subscription_type
    ).order_by('-created_at').first()
    
    valid_till = subscription.valid_till if subscription else (
        order.created_at + timedelta(
            days=order.subscription_type.duration_in_days
        )
    )
    
    # Prepare context
    invoice_context = {
        'invoice_id': str(order.id)[:8].upper(),
        'invoice_date': order.created_at.strftime('%d %b, %Y'),
        'customer_name': order.user.user.get_full_name() or order.user.user.username,
        'customer_email': order.user.user.email,
        'product_name': order.subscription_type.name,
        'product_amount': f"{order.amount:.2f}",
        'duration_days': order.subscription_type.duration_in_days,
        'platform_charges': f"{platform_charges:.2f}",
        'total_amount': f"{total_amount:.2f}",
        'payment_method': 'Razorpay',
        'transaction_id': order.razorpay_payment_id or 'N/A',
        'valid_till': valid_till.strftime('%d %b, %Y'),
    }
    
    # Render and send
    from django.template.loader import render_to_string
    html_message = render_to_string(
        'subscription_invoice.html',
        invoice_context
    )
    
    from apps.messaging.smtp import send_email
    send_email.delay(
        'subscription_invoice',
        f'Invoice for {order.subscription_type.name} Subscription',
        order.user.user.email,
        html_message=html_message,
    )
    
    return Response({
        "status": True,
        "message": "Invoice generated and sent to email"
    })
```


SMTP INTEGRATION:
=================

File: apps/messaging/smtp.py

The send_email task should support html_message parameter:

```python
@shared_task
def send_email(
    template_name: str,
    subject: str,
    recipient_email: str,
    html_message: str = None,
    **context
):
    """
    Send email with optional HTML message.
    
    Args:
        template_name: Name of email template
        subject: Email subject
        recipient_email: Recipient email address
        html_message: Pre-rendered HTML (optional)
        **context: Additional context variables
    """
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    
    # Use provided HTML or render from template
    if html_message:
        html_content = html_message
    else:
        html_content = render_to_string(
            f'{template_name}.html',
            context
        )
    
    # Create email
    email = EmailMultiAlternatives(
        subject=subject,
        body=strip_tags(html_content),  # Plain text fallback
        from_email=settings.DEFAULT_FROM_MAIL,
        to=[recipient_email]
    )
    
    # Attach HTML
    email.attach_alternative(html_content, "text/html")
    
    # Send
    email.send()
```


TESTING THE INVOICE:
====================

1. MANUAL TESTING:

```python
# In Django shell
from apps.users.models import SubscriptionOrder, SubscriptionType, UserProfile
from django.template.loader import render_to_string
from decimal import Decimal

# Get test data
order = SubscriptionOrder.objects.first()
platform_charges = order.amount * Decimal('0.02')
total_amount = order.amount + platform_charges

# Prepare context
invoice_context = {
    'invoice_id': 'TEST001',
    'invoice_date': '15 Jan, 2024',
    'customer_name': 'Test User',
    'customer_email': 'test@example.com',
    'product_name': 'Premium Plan',
    'product_amount': '99.99',
    'duration_days': 30,
    'platform_charges': f"{platform_charges:.2f}",
    'total_amount': f"{total_amount:.2f}",
    'payment_method': 'Razorpay',
    'transaction_id': 'pay_test123',
    'valid_till': '15 Feb, 2024',
}

# Render
html = render_to_string('subscription_invoice.html', invoice_context)

# Save to file for preview
with open('/tmp/invoice.html', 'w') as f:
    f.write(html)

# Open in browser: file:///tmp/invoice.html
```

2. EMAIL TESTING:

```python
# Send test email
from apps.messaging.smtp import send_email

send_email.delay(
    'subscription_invoice',
    'Test Invoice',
    'your-email@example.com',
    html_message=html,
)
```

3. AUTOMATED TESTING:

```python
# In tests.py
from django.test import TestCase
from django.template.loader import render_to_string

class InvoiceTemplateTest(TestCase):
    def test_invoice_renders(self):
        context = {
            'invoice_id': 'TEST001',
            'invoice_date': '15 Jan, 2024',
            'customer_name': 'Test User',
            'customer_email': 'test@example.com',
            'product_name': 'Premium Plan',
            'product_amount': '99.99',
            'duration_days': 30,
            'platform_charges': '2.00',
            'total_amount': '101.99',
            'payment_method': 'Razorpay',
            'transaction_id': 'pay_test123',
            'valid_till': '15 Feb, 2024',
        }
        
        html = render_to_string('subscription_invoice.html', context)
        
        # Verify key elements
        self.assertIn('TEST001', html)
        self.assertIn('Test User', html)
        self.assertIn('Premium Plan', html)
        self.assertIn('₹99.99', html)
        self.assertIn('₹2.00', html)
        self.assertIn('₹101.99', html)
        self.assertIn('pay_test123', html)
```


CUSTOMIZATION EXAMPLES:
=======================

1. CHANGE PLATFORM CHARGES PERCENTAGE:

Current: 2%
```python
platform_charges = order.amount * Decimal('0.02')
```

Change to 3%:
```python
platform_charges = order.amount * Decimal('0.03')
```

2. ADD DISCOUNT:

```python
discount = order.amount * Decimal('0.10')  # 10% discount
subtotal = order.amount - discount
platform_charges = subtotal * Decimal('0.02')
total_amount = subtotal + platform_charges

invoice_context = {
    ...
    'discount': f"{discount:.2f}",
    'subtotal_after_discount': f"{subtotal:.2f}",
    ...
}
```

3. ADD TAX:

```python
tax = order.amount * Decimal('0.18')  # 18% GST
total_amount = order.amount + tax

invoice_context = {
    ...
    'tax': f"{tax:.2f}",
    'tax_label': 'GST (18%)',
    ...
}
```

4. CHANGE CURRENCY:

Replace ₹ with your currency symbol in:
- Template: subscription_invoice.html
- Backend: invoice_context variables


TROUBLESHOOTING:
================

Issue: Template not rendering
Solution: Check template path is correct
  - Path: apps/messaging/templates/subscription_invoice.html
  - Verify TEMPLATES setting in settings.py

Issue: Variables showing as empty
Solution: Ensure all required variables are in context
  - Check variable names match exactly
  - Verify data types (string, not object)

Issue: Email not sending
Solution: Check Celery and email configuration
  - Verify CELERY_BROKER_URL
  - Check email backend in settings.py
  - Verify SMTP credentials

Issue: Styling looks broken
Solution: Email client compatibility
  - Test in multiple clients
  - Use inline CSS (already done)
  - Avoid external stylesheets

Issue: Currency symbol not displaying
Solution: Ensure UTF-8 encoding
  - Add to email headers: charset='utf-8'
  - Verify database encoding


PERFORMANCE CONSIDERATIONS:
===========================

1. Template Rendering:
   - Rendering is fast (< 100ms)
   - No database queries in template
   - Minimal string operations

2. Email Sending:
   - Async via Celery (non-blocking)
   - Delayed task execution
   - Retry on failure

3. Optimization Tips:
   - Cache template if rendering multiple times
   - Use Celery for batch email sending
   - Monitor email delivery rates


SECURITY CONSIDERATIONS:
========================

1. Data Validation:
   - Verify order belongs to user
   - Validate all amounts
   - Check payment status

2. Email Security:
   - Use HTTPS for links
   - Validate email addresses
   - Sanitize user input

3. Payment Security:
   - Verify Razorpay signature
   - Use secure API keys
   - Never expose secrets in template


MONITORING & LOGGING:
====================

Add logging to track invoice generation:

```python
import logging

logger = logging.getLogger(__name__)

def generate_invoice(request):
    try:
        logger.info(f"Generating invoice for order {order_id}")
        # ... code ...
        logger.info(f"Invoice sent to {order.user.user.email}")
    except Exception as e:
        logger.error(f"Invoice generation failed: {str(e)}")
        raise
```


FUTURE ENHANCEMENTS:
====================

1. PDF Generation:
   - Convert HTML to PDF
   - Send PDF attachment
   - Store PDF for records

2. Invoice Numbering:
   - Sequential invoice numbers
   - Custom prefix/suffix
   - Date-based numbering

3. Multi-language Support:
   - Translate template text
   - Localize currency
   - Format dates by locale

4. Advanced Analytics:
   - Track invoice views
   - Monitor email delivery
   - Analyze payment patterns

5. Recurring Invoices:
   - Auto-generate for renewals
   - Scheduled email sending
   - Subscription management
"""
