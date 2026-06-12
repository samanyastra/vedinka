# Bill Breakdown Handler - Usage Guide

The `BillBreakdownHandler` calculates bill breakdowns with charges (platform fees, GST, shipping, etc.) before any transaction is processed. It mirrors the robustness of `TransactionHandler`.

## Overview

**Two Main Functions:**
1. **Get Bill Breakdown** - Calculate charges and generate breakdown
2. **Create Invoice Dictionary** - Generate invoice-ready data for emails/display

**Bill Ledger** - Automatic audit trail storage of all breakdowns

## Setup: Define Charges

Create charges via admin API or Django admin:

```python
# Example 1: Percentage charge (GST)
POST /api/finance/charges/create/
{
  "name": "GST",
  "description": "Goods and Services Tax",
  "amount_type": "%",
  "amount": 18,
  "is_active": true,
  "apply_to_order": true,
  "apply_to_subscription": true
}

# Example 2: Fixed amount charge (Shipping)
POST /api/finance/charges/create/
{
  "name": "Shipping Charges",
  "description": "Flat shipping fee",
  "amount_type": "INR",
  "amount": 200,
  "is_active": true,
  "apply_to_order": true,
  "apply_to_subscription": false
}

# Example 3: Platform fee (5%)
POST /api/finance/charges/create/
{
  "name": "Platform Fee",
  "description": "Vedinka platform processing fee",
  "amount_type": "%",
  "amount": 5,
  "is_active": true,
  "apply_to_order": true,
  "apply_to_subscription": true
}
```

## Usage Pattern 1: Book Order

```python
from apps.finance.bill_breakdown_handler import BillBreakdownHandler

# Step 1: Create breakdown handler
handler = BillBreakdownHandler(
    user_id=123,
    subtotal=1000.00,
    transaction_type="ORDER",
    reference_id="ORDER_ABC123"
)

# Step 2: Get breakdown
breakdown = handler.calculate_breakdown()
# Returns:
# {
#   "subtotal": 1000.0,
#   "lines": [
#     {
#       "name": "Platform Fee",
#       "amount_type": "%",
#       "charge_value": 5,
#       "calculated_amount": 50.0
#     },
#     {
#       "name": "GST",
#       "amount_type": "%",
#       "charge_value": 18,
#       "calculated_amount": 180.0
#     },
#     {
#       "name": "Shipping",
#       "amount_type": "INR",
#       "charge_value": 200,
#       "calculated_amount": 200.0
#     }
#   ],
#   "total_charges": 430.0,
#   "final_amount": 1430.0
# }

# Step 3: Save to ledger (audit trail)
bill_ledger = handler.save_bill_ledger()

# Step 4: Create invoice dictionary (for email/display)
invoice = handler.create_invoice_dict()
# Returns:
# {
#   "customer_name": "John Doe",
#   "customer_email": "john@example.com",
#   "transaction_type": "ORDER",
#   "reference_id": "ORDER_ABC123",
#   "subtotal": 1000.0,
#   "charges": [...charge lines...],
#   "total_charges": 430.0,
#   "final_amount": 1430.0,
#   "currency": "INR"
# }

# Step 5: Use final_amount for TransactionHandler
from apps.finance.transaction_handler import TransactionHandler

tx_handler = TransactionHandler(
    user_id=123,
    transaction_amount=handler.final_amount,  # Use breakdown amount!
    actual_amount=1000.00  # Original subtotal for records
)
```

## Usage Pattern 2: Subscription

```python
from apps.finance.bill_breakdown_handler import BillBreakdownHandler

handler = BillBreakdownHandler(
    user_id=456,
    subtotal=299.00,
    transaction_type="SUBSCRIPTION",
    reference_id="SUBSCRIPTION_XYZ789"
)

breakdown = handler.calculate_breakdown()
# Only applies charges with apply_to_subscription=true

bill_ledger = handler.save_bill_ledger()
invoice = handler.create_invoice_dict()

# Pass final amount to transaction
final_amount = handler.final_amount
```

## Usage Pattern 3: Custom Charges

```python
from apps.finance.bill_breakdown_handler import BillBreakdownHandler
from apps.finance.models import Charge

# Create temp charge objects (not saved to DB)
custom_charges = [
    Charge(
        name="Early Bird Discount",
        amount_type="%",
        amount=-10,  # Negative = discount
        is_active=True
    )
]

handler = BillBreakdownHandler(
    user_id=789,
    subtotal=500.00,
    transaction_type="ORDER",
    reference_id="ORDER_DISCOUNT",
    custom_charges=custom_charges
)

breakdown = handler.calculate_breakdown()
# Will apply standard charges + custom discount
```

## API Endpoints

### Admin Charge Management

```
GET    /api/finance/charges/                 # List all charges
POST   /api/finance/charges/create/          # Create charge
PUT    /api/finance/charges/<id>/update/     # Update charge
DELETE /api/finance/charges/<id>/delete/     # Delete charge
```

### Bill Ledger View

```
GET /api/finance/ledger/                     # List all bill ledger entries
GET /api/finance/ledger/?transaction_type=ORDER   # Filter by type
GET /api/finance/ledger/?user_id=123         # Filter by user
GET /api/finance/ledger/<id>/                # Get specific entry
```

## Key Features

1. **Flexible Charges** - Support both % and INR amount types
2. **Transaction Type Specific** - Different charges for orders vs subscriptions
3. **Activation Control** - Enable/disable charges without deletion
4. **Audit Trail** - All breakdowns saved in BillLedger
5. **Invoice Generation** - Ready-to-use dictionary for email templates
6. **Validation** - Prevents invalid amounts and configurations
7. **Breakdown Summary** - Text summary for logging/debugging

## Breakdown Summary

```python
summary = handler.get_breakdown_summary()
# Output:
# Subtotal: ₹1000.0
# Platform Fee: ₹50.0 (%)
# GST: ₹180.0 (%)
# Shipping: ₹200.0 (INR)
# Total Charges: ₹430.0
# Final Amount: ₹1430.0
```

## Integration with TransactionHandler

**Flow:**
1. Create BillBreakdownHandler → calculate breakdown
2. Save to bill ledger (audit trail)
3. Create invoice dict (for email)
4. Pass `handler.final_amount` to TransactionHandler
5. TransactionHandler creates gateway order with final amount
6. After payment success, use invoice dict for email template

## Models

### Charge
- `name` - Charge name (e.g., "Platform Fee", "GST")
- `amount_type` - '%' or 'INR'
- `amount` - Value (e.g., 5 for 5%, 200 for ₹200)
- `is_active` - Enable/disable
- `apply_to_order` - Apply to book orders
- `apply_to_subscription` - Apply to subscriptions

### BillLedger
- `user` - User who received the bill
- `transaction_type` - ORDER, SUBSCRIPTION, REFUND
- `reference_id` - Order/Payment/Subscription ID
- `subtotal` - Original amount
- `breakdown_json` - Complete breakdown details
- `total_charges` - Sum of all charges
- `final_amount` - Subtotal + charges

### BillLine (Internal)
- Used internally for breakdown calculations
- Stores individual line items
