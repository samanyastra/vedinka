# Bill Breakdown System - Quick Setup

## 1. Run Migrations

```bash
# Create migrations for new models
python manage.py makemigrations finance

# Apply migrations
python manage.py migrate finance

# Verify tables created
python manage.py dbshell
# Check tables: finance_charge, finance_billline, finance_billledger
```

## 2. Create Initial Charges (Choose One Method)

### Method A: Django Shell

```bash
python manage.py shell
```

```python
from apps.finance.models import Charge

# GST - 18%
Charge.objects.create(
    name="GST",
    description="Goods and Services Tax",
    amount_type="%",
    amount=18,
    is_active=True,
    apply_to_order=True,
    apply_to_subscription=True
)

# Platform Fee - 5%
Charge.objects.create(
    name="Platform Fee",
    description="Vedinka platform processing fee",
    amount_type="%",
    amount=5,
    is_active=True,
    apply_to_order=True,
    apply_to_subscription=True
)

# Shipping - ₹200 (Orders only)
Charge.objects.create(
    name="Shipping Charges",
    description="Standard shipping fee",
    amount_type="INR",
    amount=200,
    is_active=True,
    apply_to_order=True,
    apply_to_subscription=False
)

# Verify
Charge.objects.all().values()
exit()
```

### Method B: API Endpoint

```bash
# Assuming server is running on http://localhost:8000
# You need admin token

# Create GST
curl -X POST http://localhost:8000/api/finance/charges/create/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GST",
    "description": "Goods and Services Tax",
    "amount_type": "%",
    "amount": 18,
    "is_active": true,
    "apply_to_order": true,
    "apply_to_subscription": true
  }'

# Create Platform Fee
curl -X POST http://localhost:8000/api/finance/charges/create/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Platform Fee",
    "description": "Vedinka platform processing fee",
    "amount_type": "%",
    "amount": 5,
    "is_active": true,
    "apply_to_order": true,
    "apply_to_subscription": true
  }'

# Create Shipping
curl -X POST http://localhost:8000/api/finance/charges/create/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Shipping Charges",
    "description": "Standard shipping fee",
    "amount_type": "INR",
    "amount": 200,
    "is_active": true,
    "apply_to_order": true,
    "apply_to_subscription": false
  }'

# List all charges
curl http://localhost:8000/api/finance/charges/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Method C: Django Admin Panel

1. Go to `/admin/finance/charge/`
2. Click "Add Charge"
3. Fill in the form:
   - Name: "GST"
   - Description: "Goods and Services Tax"
   - Amount Type: "%"
   - Amount: 18
   - Is Active: ✓
   - Apply to Order: ✓
   - Apply to Subscription: ✓
4. Save and repeat for other charges

## 3. Test the Handler

```bash
python manage.py shell
```

```python
from apps.finance.bill_breakdown_handler import BillBreakdownHandler
from django.contrib.auth import get_user_model

User = get_user_model()

# Get a test user
user = User.objects.first()

# Create handler
handler = BillBreakdownHandler(
    user_id=user.id,
    subtotal=1000,
    transaction_type="ORDER",
    reference_id="TEST_ORDER_001"
)

# Calculate breakdown
breakdown = handler.calculate_breakdown()
print("Breakdown:")
print(handler.get_breakdown_summary())

# Save to ledger
bill_ledger = handler.save_bill_ledger()
print(f"\nBill Ledger ID: {bill_ledger.id}")

# Create invoice dict
invoice = handler.create_invoice_dict()
print(f"\nInvoice: {invoice}")

exit()
```

Expected output:
```
Breakdown:
Subtotal: ₹1000.0
Platform Fee: ₹50.0 (%)
GST: ₹180.0 (%)
Shipping: ₹200.0 (INR)
Total Charges: ₹430.0
Final Amount: ₹1430.0

Bill Ledger ID: 1

Invoice: {...full invoice dict...}
```

## 4. Verify in Admin

```bash
# Check created ledger entries
curl http://localhost:8000/api/finance/ledger/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## 5. Integration Checklist

- [ ] Run migrations
- [ ] Create initial charges
- [ ] Test handler manually
- [ ] Update subscription verification endpoint (subscribe with BillBreakdownHandler)
- [ ] Update cart checkout endpoint (checkout with BillBreakdownHandler)
- [ ] Update email templates to use breakdown
- [ ] Test full flow: Order → Breakdown → Payment → Email
- [ ] Add admin dashboard metrics for bills

## Common Issues

### Issue: "Charge not found"
- Solution: Verify charges exist: `Charge.objects.all()`
- Check `is_active=True` and appropriate `apply_to_*` flags

### Issue: "Final amount is same as subtotal"
- Solution: Ensure charges have `is_active=True`
- Check transaction_type matches charge configuration

### Issue: "Migration errors"
- Solution: 
  ```bash
  python manage.py makemigrations --empty finance --name fix_charge
  python manage.py migrate finance
  ```

## Query Examples

```python
# All active charges
Charge.objects.filter(is_active=True)

# Charges for subscriptions only
Charge.objects.filter(is_active=True, apply_to_subscription=True)

# Recent bills
BillLedger.objects.order_by('-created_at')[:10]

# Bills for a specific user
BillLedger.objects.filter(user_id=123)

# Bills by transaction type
BillLedger.objects.filter(transaction_type='ORDER')

# Total charges collected from bills
from django.db.models import Sum
BillLedger.objects.aggregate(total=Sum('total_charges'))
```

## Admin Dashboard Metrics

```python
# Cards to show in admin dashboard
from django.db.models import Sum
from apps.finance.models import BillLedger

# Total revenue (before payment gateway fees)
total_revenue = BillLedger.objects.aggregate(
    total=Sum('final_amount')
)['total']

# Total charges collected
total_charges = BillLedger.objects.aggregate(
    total=Sum('total_charges')
)['total']

# Breakdown by transaction type
breakdown_by_type = BillLedger.objects.values(
    'transaction_type'
).annotate(
    total=Sum('final_amount'),
    count=Count('id')
)

# Daily revenue
from datetime import date
today_revenue = BillLedger.objects.filter(
    created_at__date=date.today()
).aggregate(
    total=Sum('final_amount')
)['total']
```

## Performance Optimization

For high-volume transactions, consider:

1. **Index on BillLedger**
```python
# Already in model, but ensure migration runs
indexes = [
    models.Index(fields=['user', '-created_at']),
    models.Index(fields=['reference_id']),
]
```

2. **Batch Operations**
```python
# Instead of looping
for order in orders:
    breakdown = BillBreakdownHandler(...)
    
# Use bulk operations if needed
BillLedger.objects.bulk_create([...])
```

3. **Cache Charges**
```python
from django.core.cache import cache

def get_active_charges():
    charges = cache.get('active_charges')
    if charges is None:
        charges = list(Charge.objects.filter(is_active=True))
        cache.set('active_charges', charges, 3600)  # 1 hour
    return charges
```

## Rollback (if needed)

```bash
# Remove migrations
python manage.py migrate finance 0001_initial  # Or previous migration

# Delete migration files
rm apps/finance/migrations/0XXX_charge_billline_billledger.py

# Recreate when ready
python manage.py makemigrations finance
python manage.py migrate finance
```
