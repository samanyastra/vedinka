"""
USER SUBSCRIPTION APIs - Documentation
========================================

These 5 APIs enable authenticated users to view, purchase, and manage subscriptions.
All endpoints require JWT authentication (Bearer token).

Base URL: /api/users/my-subscriptions/

1. GET /my-subscription/
   ========================
   Summary: Get my subscription
   Description: Retrieve current active subscription of authenticated user
   
   Authentication: Required (IsAuthenticated)
   Method: GET
   
   Response (200 OK):
   {
       "id": "uuid",
       "subscription_name": "Premium",
       "subscription_cost": "99.99",
       "subscription_duration": 30,
       "subscription_features": "Feature list",
       "subscribed_at": "2024-01-15T10:30:00Z",
       "valid_till": "2024-02-15T10:30:00Z",
       "is_active": true,
       "days_remaining": 15
   }
   
   Error (404):
   {
       "error": "No active subscription found"
   }


2. GET /available-subscriptions/
   ==============================
   Summary: View all available subscriptions
   Description: Get all available subscription types with current purchase status
   
   Authentication: Required (IsAuthenticated)
   Method: GET
   
   Response (200 OK):
   [
       {
           "id": "uuid",
           "name": "Premium",
           "cost": "99.99",
           "currency": "INR",
           "duration_in_days": 30,
           "features": "Feature list",
           "is_purchased": true,
           "current_subscription": {
               "id": "uuid",
               "subscribed_at": "2024-01-15T10:30:00Z",
               "valid_till": "2024-02-15T10:30:00Z"
           }
       },
       {
           "id": "uuid",
           "name": "Basic",
           "cost": "49.99",
           "currency": "INR",
           "duration_in_days": 30,
           "features": "Feature list",
           "is_purchased": false,
           "current_subscription": null
       }
   ]


3. POST /create-order/
   ====================
   Summary: Create subscription order
   Description: Create Razorpay order for subscription purchase
   
   Authentication: Required (IsAuthenticated)
   Method: POST
   
   Request Body:
   {
       "subscription_type_id": "uuid"
   }
   
   Response (201 Created):
   {
       "id": "uuid",
       "razorpay_order_id": "order_1234567890",
       "subscription_name": "Premium",
       "amount": "99.99",
       "currency": "INR",
       "payment_status": "pending",
       "created_at": "2024-01-15T10:30:00Z"
   }
   
   Error (400):
   {
       "error": "Subscription type not found"
   }


4. POST /verify-payment/
   ======================
   Summary: Verify payment
   Description: Verify Razorpay payment and activate subscription
   
   Authentication: Required (IsAuthenticated)
   Method: POST
   
   Request Body:
   {
       "razorpay_order_id": "order_1234567890",
       "razorpay_payment_id": "pay_1234567890",
       "razorpay_signature": "signature_hash"
   }
   
   Response (200 OK):
   {
       "status": true,
       "message": "Payment verified and subscription activated"
   }
   
   Process:
   - Verifies Razorpay signature
   - Updates order payment status to 'completed'
   - Creates UserSubscription record with valid_till date
   - Sends confirmation email to user
   
   Error (400):
   {
       "error": "Invalid payment signature"
   }


5. GET /generate-invoice/
   =======================
   Summary: Generate invoice
   Description: Generate and send invoice for subscription purchase
   
   Authentication: Required (IsAuthenticated)
   Method: GET
   Query Parameters:
   - order_id (required): UUID of the subscription order
   
   URL Example: /generate-invoice/?order_id=uuid
   
   Response (200 OK):
   {
       "status": true,
       "message": "Invoice generated and sent to email"
   }
   
   Process:
   - Retrieves order details
   - Verifies order belongs to current user
   - Generates invoice with order information
   - Sends invoice to user's email
   
   Error (404):
   {
       "error": "Order not found"
   }
   
   Error (403):
   {
       "error": "Unauthorized"
   }


WORKFLOW EXAMPLE:
=================

1. User calls GET /available-subscriptions/ to see all plans
2. User calls POST /create-order/ with subscription_type_id
3. Frontend receives razorpay_order_id and initializes Razorpay payment
4. After payment, frontend calls POST /verify-payment/ with payment details
5. Backend verifies signature and creates subscription
6. User can call GET /my-subscription/ to view active subscription
7. User can call GET /generate-invoice/ to get invoice


MODELS:
=======

SubscriptionOrder:
- id (UUID)
- user (ForeignKey to UserProfile)
- subscription_type (ForeignKey to SubscriptionType)
- razorpay_order_id (CharField, unique)
- amount (DecimalField)
- currency (CharField)
- payment_status (CharField: pending, completed, failed, cancelled)
- razorpay_payment_id (CharField, nullable)
- razorpay_signature (CharField, nullable)
- created_at (DateTimeField)
- updated_at (DateTimeField)

UserSubscription (existing):
- id (UUID)
- user (ForeignKey to UserProfile)
- subscription_type (ForeignKey to SubscriptionType)
- subscribed_at (DateTimeField)
- valid_till (DateTimeField)


CONFIGURATION:
==============

Add to .env:
RAZORPAY_KEY_ID=<your_razorpay_key_id>
RAZORPAY_KEY_SECRET=<your_razorpay_key_secret>

These are added to settings.py as:
RAZORPAY_KEY_ID = env('RAZORPAY_KEY_ID', default='<razorpay_key_id>')
RAZORPAY_KEY_SECRET = env('RAZORPAY_KEY_SECRET', default='<razorpay_key_secret>')
"""
