# Bill Breakdown System - Architecture Summary

## Overview

A robust, production-ready bill breakdown system that calculates charges (platform fees, GST, shipping) before payment transactions. Follows the same patterns as `TransactionHandler` for consistency and maintainability.

## Components

### 1. Models (`apps/finance/models.py`)

**Charge**
- Charge templates defining platform-level fees/taxes
- Flexible amount types: percentage (%) or fixed INR
- Activation control: enable/disable without deletion
- Transaction-type specific: different charges for orders vs subscriptions
- Fields: name, amount_type, amount, is_active, apply_to_order, apply_to_subscription

**BillLine**
- Individual line items in a breakdown
- Stores name, amount_type, base_amount, calculated_amount
- Temporary data structure for calculations

**BillLedger**
- Permanent audit trail of all bill breakdowns
- Stores complete breakdown JSON with line items
- Links to user, transaction type, and reference ID
- Final amounts for reconciliation
- Fields: user, transaction_type, reference_id, subtotal, breakdown_json, total_charges, final_amount

### 2. Handler (`apps/finance/bill_breakdown_handler.py`)

**BillBreakdownHandler Class**

Methods:
- `calculate_breakdown()` - Compute all charges, returns breakdown dict
- `create_invoice_dict()` - Generate invoice-ready dictionary for emails
- `save_bill_ledger()` - Store breakdown to BillLedger for audit trail
- `get_breakdown_summary()` - Text summary for logging

Features:
- Loads charges from DB based on transaction type
- Supports custom charges via constructor
- Handles both % and INR calculations
- Validates user and amounts
- Returns structured data ready for TransactionHandler

### 3. Serializers (`apps/finance/bill_serializers.py`)

- `ChargeSerializer` - For charge CRUD operations
- `BillLineSerializer` - For breakdown line items
- `BillLedgerSerializer` - For ledger entries
- `BillBreakdownResponseSerializer` - For API responses

### 4. Admin Views (`apps/finance/bill_views.py`)

Charge Management:
- `list_charges()` - GET all charges
- `create_charge()` - POST new charge
- `update_charge()` - PUT/PATCH existing charge
- `delete_charge()` - DELETE charge

Bill Ledger:
- `list_bill_ledger()` - GET all ledger entries (with filters)
- `get_bill_ledger_entry()` - GET specific entry

All endpoints require `IsSuperUserOrAdmin` permission.

### 5. URLs (`apps/finance/bill_urls.py`)

Routes:
```
/api/finance/charges/              - List charges
/api/finance/charges/create/       - Create charge
/api/finance/charges/<id>/update/  - Update charge
/api/finance/charges/<id>/delete/  - Delete charge
/api/finance/ledger/               - List ledger (with filters)
/api/finance/ledger/<id>/          - Get specific ledger entry
```

## Charge Types Supported

### 1. Percentage Charge
```json
{
  "name": "GST",
  "amount_type": "%",
  "amount": 18
}
```
Calculates 18% of subtotal.

### 2. Fixed Amount Charge
```json
{
  "name": "Shipping",
  "amount_type": "INR",
  "amount": 200
}
```
Adds flat ₹200 to bill.

### 3. Negative Charges (Discounts)
```json
{
  "name": "Early Bird Discount",
  "amount_type": "%",
  "amount": -10
}
```
Subtracts 10% from subtotal.

## Usage Workflow

**Step-by-Step Flow:**

1. **Setup** - Define charges in admin panel
   ```
   POST /api/finance/charges/create/
   - Platform Fee: 5%
   - GST: 18%
   - Shipping: ₹200
   ```

2. **Calculate** - Create handler and get breakdown
   ```python
   handler = BillBreakdownHandler(
       user_id=123,
       subtotal=1000,
       transaction_type="ORDER"
   )
   breakdown = handler.calculate_breakdown()
   # subtotal: 1000
   # charges: [50, 180, 200]
   # final: 1430
   ```

3. **Audit** - Save to ledger
   ```python
   bill_ledger = handler.save_bill_ledger()
   # Stored in BillLedger table with full breakdown
   ```

4. **Invoice** - Generate email data
   ```python
   invoice = handler.create_invoice_dict()
   # Ready for email template rendering
   ```

5. **Payment** - Use final amount for transaction
   ```python
   tx_handler = TransactionHandler(
       user_id=123,
       transaction_amount=handler.final_amount  # 1430
   )
   ```

## Data Flow Diagram

```
User Places Order (₹1000)
         ↓
[BillBreakdownHandler]
    - Load charges (Platform 5%, GST 18%, Shipping 200)
    - Calculate breakdown
    - Subtotal: ₹1000
    - Platform Fee: ₹50 (5%)
    - GST: ₹180 (18%)
    - Shipping: ₹200
    - Final: ₹1430
         ↓
[Save to BillLedger] - Audit Trail
         ↓
[Create Invoice Dict] - For email template
         ↓
[TransactionHandler] - Process payment with ₹1430
         ↓
[Payment Gateway] - Razorpay/Stripe with ₹1430
         ↓
Success → Email invoice with breakdown
```

## Integration Points

### With TransactionHandler
```python
breakdown_handler = BillBreakdownHandler(...)
breakdown = breakdown_handler.calculate_breakdown()

tx_handler = TransactionHandler(
    user_id=user_id,
    transaction_amount=breakdown_handler.final_amount,  # Use this!
    actual_amount=original_subtotal
)
```

### With Email Templates
```python
invoice_dict = handler.create_invoice_dict()
# Pass to subscription_invoice.html template
render_to_string('subscription_invoice.html', invoice_dict)
```

### With Ledger Queries
```python
# Admin dashboard
ledger = BillLedger.objects.filter(
    user_id=user_id,
    transaction_type="ORDER"
).order_by('-created_at')

# Check breakdown details
for entry in ledger:
    print(entry.breakdown_json)  # Full breakdown
    print(entry.final_amount)     # Total charged
```

## Key Features

✅ **Flexible Charges** - Support % and INR amounts
✅ **Transaction-Specific** - Different charges for orders/subscriptions
✅ **Audit Trail** - Complete breakdown history in BillLedger
✅ **Invoice Ready** - Structured data for email templates
✅ **Admin Control** - Enable/disable charges without deletion
✅ **Validation** - Comprehensive error handling
✅ **Scalable** - Supports unlimited charges per transaction
✅ **Debug Friendly** - Text summaries for logging
✅ **Custom Charges** - Support for dynamic/one-off charges
✅ **Discount Support** - Negative amounts for discounts

## Error Constants Added

```python
BILL_BREAKDOWN_FAILED = "Failed to calculate bill breakdown"
INVALID_CHARGE_CONFIGURATION = "Invalid charge configuration"
CHARGE_NOT_FOUND = "Charge configuration not found"
INVALID_CHARGE_AMOUNT_TYPE = "Invalid charge amount type. Must be '%' or 'INR'"
INVALID_CHARGE_AMOUNT = "Charge amount must be greater than zero"
```

## Database Migrations Required

Run migrations after adding models:
```bash
python manage.py makemigrations finance
python manage.py migrate finance
```

This will create 3 new tables:
- `finance_charge`
- `finance_billline`
- `finance_billledger`

## Example Charges Configuration

For a complete e-commerce setup:

```python
# Platform Processing Fee - 5%
Charge.objects.create(
    name="Platform Fee",
    amount_type="%",
    amount=5,
    is_active=True,
    apply_to_order=True,
    apply_to_subscription=True
)

# GST - 18%
Charge.objects.create(
    name="GST",
    amount_type="%",
    amount=18,
    is_active=True,
    apply_to_order=True,
    apply_to_subscription=True
)

# Shipping - ₹200
Charge.objects.create(
    name="Shipping Charges",
    amount_type="INR",
    amount=200,
    is_active=True,
    apply_to_order=True,
    apply_to_subscription=False
)

# Packaging - ₹50
Charge.objects.create(
    name="Packaging",
    amount_type="INR",
    amount=50,
    is_active=True,
    apply_to_order=True,
    apply_to_subscription=False
)
```

## Files Created

1. **models.py** - Charge, BillLine, BillLedger models (updated)
2. **bill_breakdown_handler.py** - Main handler class
3. **bill_serializers.py** - API serializers
4. **bill_views.py** - Admin CRUD endpoints
5. **bill_urls.py** - URL routing
6. **urls.py** - Updated to include bill_urls (updated)
7. **errors/en.py** - New error constants (updated)
8. **BILL_BREAKDOWN_GUIDE.md** - Complete usage guide
9. **BILL_BREAKDOWN_INTEGRATION.md** - Integration patterns

## Next Steps

1. Run migrations to create tables
2. Create charges in admin panel (or via API)
3. Integrate BillBreakdownHandler in subscription verification endpoint
4. Integrate BillBreakdownHandler in cart checkout endpoint
5. Update email templates to include breakdown details
6. Add bill breakdown metrics to admin dashboard
