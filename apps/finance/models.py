from django.db import models
from apps.common.models import TransactionStatus, PromoCode, BaseModel


class PromoCodeLog(BaseModel):
    """Log of promo code usage"""
    user = models.ForeignKey(
        'users.UserProfile',
        on_delete=models.CASCADE,
        related_name='promo_code_logs'
    )
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-used_at']
        indexes = [
            models.Index(fields=['user', '-used_at']),
        ]
    
    def __str__(self):
        return f"{self.user.user.username} - {self.promo_code.code} ({self.discount_applied})"


class Order(BaseModel):
    """Customer orders"""
    local_order_id = models.CharField(max_length=100, unique=True)
    client_order_id = models.CharField(max_length=100, blank=True, null=True, help_text="Gateway reference ID")
    user = models.ForeignKey(
        'users.UserProfile',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    transaction_status = models.ForeignKey(
        TransactionStatus,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    order_date = models.DateField()
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['local_order_id']),
        ]
    
    def __str__(self):
        return f"Order {self.local_order_id}"


class OrderItem(BaseModel):
    """Individual items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(
        'content.Book',
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.order.local_order_id} - {self.book.title}"


class Payment(BaseModel):
    """Payment transactions"""
    GATEWAY_CHOICES = [
        ('razorpay', 'Razorpay'),
        ('stripe', 'Stripe'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    gateway_payment_id = models.CharField(max_length=200)
    gateway_order_id = models.CharField(max_length=200)
    status = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    raw_response = models.JSONField(help_text="Raw response from payment gateway")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gateway_payment_id']),
            models.Index(fields=['gateway_order_id']),
        ]
    
    def __str__(self):
        return f"Payment {self.gateway_payment_id}"


class Payout(BaseModel):
    """Author payouts"""
    PAYOUT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
    ]
    
    user = models.ForeignKey(
        'users.UserProfile',
        on_delete=models.CASCADE,
        related_name='payouts',
        help_text='Author'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYOUT_STATUS_CHOICES, default='PENDING')
    payout_reference = models.CharField(max_length=200, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"Payout {self.id} - {self.user.user.username}"


class Ledger(BaseModel):
    """Financial ledger for tracking all transactions"""
    ENTRY_TYPE_CHOICES = [
        ('SALE', 'Sale'),
        ('REFUND', 'Refund'),
        ('PAYOUT', 'Payout'),
    ]
    
    REFERENCE_TYPE_CHOICES = [
        ('ORDER', 'Order'),
        ('PAYMENT', 'Payment'),
        ('PAYOUT', 'Payout'),
    ]
    
    user = models.ForeignKey(
        'users.UserProfile',
        on_delete=models.CASCADE,
        related_name='ledger_entries'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Positive for income, negative for expense"
    )
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE_CHOICES)
    reference_type = models.CharField(max_length=20, choices=REFERENCE_TYPE_CHOICES)
    reference_id = models.IntegerField()
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]
    
    def __str__(self):
        return f"Ledger {self.id} - {self.user.user.username}"


class BookSalesMetrics(BaseModel):
    """Monthly sales metrics per book"""
    book = models.ForeignKey(
        'content.Book',
        on_delete=models.CASCADE,
        related_name='sales_metrics'
    )
    month = models.DateField(help_text="First day of the month (YYYY-MM-01)")
    sales_count = models.IntegerField(default=0, help_text="Number of units sold")
    revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Total revenue from sales"
    )
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average rating for this month"
    )
    views_count = models.IntegerField(default=0, help_text="Page views for this month")
    
    class Meta:
        ordering = ['-month']
        unique_together = ('book', 'month')
        indexes = [
            models.Index(fields=['book', '-month']),
            models.Index(fields=['-month']),
        ]
    
    def __str__(self):
        return f"{self.book.title} - {self.month.strftime('%B %Y')} ({self.sales_count} sales)"


class AuthorSalesMetrics(BaseModel):
    """Monthly sales metrics per author"""
    author = models.ForeignKey(
        'users.UserProfile',
        on_delete=models.CASCADE,
        related_name='author_sales_metrics'
    )
    month = models.DateField(help_text="First day of the month (YYYY-MM-01)")
    total_sales_count = models.IntegerField(default=0, help_text="Total units sold")
    total_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Total revenue from all books"
    )
    book_count = models.IntegerField(default=0, help_text="Number of unique books sold")
    total_views = models.IntegerField(default=0, help_text="Total page views")
    
    class Meta:
        ordering = ['-month']
        unique_together = ('author', 'month')
        indexes = [
            models.Index(fields=['author', '-month']),
            models.Index(fields=['-month']),
        ]
    
    def __str__(self):
        return f"{self.author.user.username} - {self.month.strftime('%B %Y')} ({self.total_sales_count} sales)"


class Cart(BaseModel):
    """Shopping cart for users"""
    user = models.OneToOneField(
        'users.UserProfile',
        on_delete=models.CASCADE,
        related_name='cart'
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Cart - {self.user.user.username}"


class CartItem(BaseModel):
    """Individual items in a shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(
        'content.Book',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.IntegerField(default=1, help_text="Quantity of the book in cart")
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('cart', 'book')
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['cart', '-added_at']),
        ]
    
    def __str__(self):
        return f"{self.cart.user.user.username} - {self.book.title} (qty: {self.quantity})"


class Charge(BaseModel):
    """Charge templates for bill breakdown"""
    AMOUNT_TYPE_CHOICES = [
        ('%', 'Percentage'),
        ('INR', 'Fixed Amount (INR)'),
    ]
    
    name = models.CharField(max_length=100, help_text="Charge name (e.g., Platform Fee, GST, Shipping)")
    description = models.TextField(blank=True, help_text="Charge description")
    amount_type = models.CharField(max_length=10, choices=AMOUNT_TYPE_CHOICES, help_text="% or INR")
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount value (e.g., 5 for 5% or 200 for 200 INR)"
    )
    is_active = models.BooleanField(default=True, help_text="Enable/disable charge application")
    apply_to_order = models.BooleanField(default=True, help_text="Apply to book orders")
    apply_to_subscription = models.BooleanField(default=True, help_text="Apply to subscriptions")
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.amount}{self.amount_type})"


class BillLine(BaseModel):
    """Individual line item in a bill breakdown"""
    name = models.CharField(max_length=100, help_text="Line item name")
    amount_type = models.CharField(max_length=10, choices=Charge.AMOUNT_TYPE_CHOICES)
    base_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Base amount for % calculations"
    )
    calculated_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Final calculated amount after % application"
    )
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name}: {self.calculated_amount}"


class BillLedger(BaseModel):
    """Bill breakdown ledger for audit trail"""
    TRANSACTION_TYPE_CHOICES = [
        ('ORDER', 'Book Order'),
        ('SUBSCRIPTION', 'Subscription'),
        ('REFUND', 'Refund'),
    ]
    
    user = models.ForeignKey(
        'users.UserProfile',
        on_delete=models.CASCADE,
        related_name='bill_ledgers'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    reference_id = models.CharField(max_length=100, help_text="Order ID, Payment ID, or Subscription ID")
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, help_text="Subtotal before charges")
    breakdown_json = models.JSONField(
        help_text="Complete breakdown with all charges applied",
        default=dict
    )
    total_charges = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Sum of all charges"
    )
    final_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Subtotal + total charges"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['reference_id']),
        ]
    
    def __str__(self):
        return f"Bill {self.id} - {self.user.user.username} ({self.transaction_type})"
