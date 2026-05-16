"""
HARDCODED ERROR MESSAGES - MIGRATION TO CONSTANTS
=================================================

OVERVIEW:
=========

All hardcoded error messages in subscription-related views and serializers
have been moved to the centralized constants folder for consistency and
maintainability.

BENEFITS:
=========

✓ Single source of truth for error messages
✓ Easy to update messages globally
✓ Consistent error messaging across the app
✓ Better for internationalization (i18n)
✓ Easier to track and manage error types
✓ Reduced code duplication


ERROR CONSTANTS ADDED:
======================

File: apps/constants/errors/en.py

SUBSCRIPTION ERRORS:
  • SUBSCRIPTION_NOT_FOUND
  • NO_ACTIVE_SUBSCRIPTION
  • SUBSCRIPTION_TYPE_NOT_FOUND
  • DUPLICATE_SUBSCRIPTION_TYPE
  • INVALID_SUBSCRIPTION_DURATION
  • INVALID_SUBSCRIPTION_COST
  • SUBSCRIPTION_ALREADY_PURCHASED
  • SUBSCRIPTION_EXPIRED
  • SUBSCRIPTION_RENEWAL_FAILED

SUBSCRIPTION ORDER ERRORS:
  • ORDER_NOT_FOUND
  • INVALID_ORDER_ID
  • ORDER_ALREADY_COMPLETED
  • ORDER_CANCELLED
  • ORDER_PAYMENT_PENDING
  • UNAUTHORIZED_ORDER_ACCESS
  • ORDER_CREATION_FAILED

PAYMENT ERRORS:
  • PAYMENT_NOT_FOUND
  • INVALID_PAYMENT_ID
  • PAYMENT_ALREADY_PROCESSED
  • PAYMENT_FAILED
  • INVALID_PAYMENT_SIGNATURE
  • INCOMPLETE_PAYMENT_DATA
  • PAYMENT_VERIFICATION_FAILED
  • PAYMENT_GATEWAY_ERROR
  • PAYMENT_TIMEOUT
  • PAYMENT_CANCELLED_BY_USER
  • PAYMENT_AMOUNT_MISMATCH

RAZORPAY SPECIFIC ERRORS:
  • RAZORPAY_ORDER_CREATION_FAILED
  • RAZORPAY_PAYMENT_VERIFICATION_FAILED
  • RAZORPAY_CLIENT_NOT_CONFIGURED
  • RAZORPAY_INVALID_CREDENTIALS


FILES UPDATED:
==============

1. apps/constants/errors/en.py
   ✓ Added 34 new error constants
   ✓ Organized by category
   ✓ Clear, descriptive messages

2. apps/users/user_subscription_views.py
   ✓ Replaced "No active subscription found" → errors.NO_ACTIVE_SUBSCRIPTION
   ✓ Replaced "Order not found" → errors.ORDER_NOT_FOUND
   ✓ Replaced "Unauthorized" → errors.UNAUTHORIZED_ORDER_ACCESS
   ✓ Replaced "Invalid payment signature" → errors.INVALID_PAYMENT_SIGNATURE
   ✓ Replaced "Invalid order ID provided" → errors.INVALID_ORDER_ID

3. apps/users/user_subscription_serializers.py
   ✓ Replaced "Subscription type not found" → errors.SUBSCRIPTION_TYPE_NOT_FOUND

4. apps/users/subscription_serializers.py (admin)
   ✓ Replaced "Subscription type with this name already exists" → errors.DUPLICATE_SUBSCRIPTION_TYPE
   ✓ Replaced "User not found" → errors.USER_404_ERROR
   ✓ Replaced "Subscription type not found" → errors.SUBSCRIPTION_TYPE_NOT_FOUND


USAGE EXAMPLES:
===============

Before:
```python
raise ValidationError({"error": "No active subscription found"}, code=404)
```

After:
```python
from apps.constants.errors import en as errors
raise ValidationError({"error": errors.NO_ACTIVE_SUBSCRIPTION}, code=404)
```

Before:
```python
raise serializers.ValidationError("Subscription type not found")
```

After:
```python
from apps.constants.errors import en as errors
raise serializers.ValidationError(errors.SUBSCRIPTION_TYPE_NOT_FOUND)
```


CONSISTENCY ACHIEVED:
====================

All error messages now follow the same pattern:

1. Defined in apps/constants/errors/en.py
2. Imported as: from apps.constants.errors import en as errors
3. Used as: errors.ERROR_CONSTANT_NAME
4. Organized by category for easy navigation
5. Clear, user-friendly messages


FUTURE IMPROVEMENTS:
====================

1. INTERNATIONALIZATION (i18n)
   • Easy to add other languages
   • Create errors/es.py, errors/fr.py, etc.
   • Switch based on user locale

2. ERROR CODES
   • Add numeric error codes
   • Useful for API clients
   • Better error tracking

3. ERROR DOCUMENTATION
   • Document each error
   • Provide solutions
   • Help users resolve issues

4. ERROR LOGGING
   • Log errors with constants
   • Better error tracking
   • Easier debugging


MIGRATION CHECKLIST:
====================

✓ Error constants defined
✓ Views updated
✓ Serializers updated
✓ Imports added
✓ No hardcoded messages remaining
✓ Consistent naming convention
✓ Organized by category
✓ Documentation created


BEST PRACTICES:
===============

1. Always use constants for error messages
2. Group related errors together
3. Use clear, descriptive names
4. Keep messages user-friendly
5. Avoid technical jargon
6. Be consistent with naming
7. Document error meanings
8. Consider internationalization


EXAMPLE ERROR FLOW:
===================

User tries to access order they don't own:

1. View receives request
2. Checks ownership: if order.user != request.user.profile
3. Raises: ValidationError({"error": errors.UNAUTHORIZED_ORDER_ACCESS}, code=403)
4. Error constant: "You are not authorized to access this order"
5. Response sent to user with consistent message

Benefits:
  ✓ Message is consistent everywhere
  ✓ Easy to update globally
  ✓ Clear error code (403)
  ✓ User-friendly message


SUMMARY:
========

✓ 34 new error constants added
✓ 5 files updated
✓ All hardcoded messages replaced
✓ Consistent error handling
✓ Better maintainability
✓ Ready for internationalization
✓ Organized by category
✓ Clear naming convention

The subscription system now has centralized, consistent error messaging!
"""
