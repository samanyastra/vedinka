
# GENERAL ERRORS
INVALID_UUID = 'Invalid id provided.'
INVALID_EMAIL = "Email provided is invalid."
GENERIC_INVALID_DETAILS = "Invalid Details Provided"

PASSWORD_SAME_AS_OLD="Password cannot be same as old password!"


# Token errors
EMPTY_REFRESH_TOKEN_ERROR="Refresh token cannot be empty"
INVALID_REFRESH_TOKEN = "Invalid refresh token"
REFRESH_TOKEN_NOT_FOUND_ERROR = "Refresh token not found in cookies"
FAILED_TO_BLACKLIST = "Failed to blacklist token: {0}"
TOKEN_BLACKLIST_SUCCESS = "Token blacklisted successfully"


# User Registration Errors
USER_EXISTS_ERROR = "User with this email id already exists. Use forgot password to retrive credentials."
PASSWORD_LENGTH_ERROR = "Password length should be atleast 8 characters, and not more than 16."
PASSWORD_VALIDATION_ERROR = "Password is too common or similar to user name. Password length should be between 8 to 16, contain capital, small, alphanumeric characters."
PASSWORD_MISMATCH_ERROR = "Password and confirm passwords do not match."

INVALID_VERIFICAITON_LINK="The verification link is invalid. use re-activate user to get new token link."
USER_ALREADY_ACTIVATED = "The user is already activated. Use forgot credentials to retrive your user."

# login errors
USER_404_ERROR = "User Does not exist"
INVALID_DETAILS = "email / password is incorrect"
USER_INACTIVE = "user is inactive, visit activation page to activate your vedinka acount."

# User Profile Errors
PROFILE_NOT_FOUND = "User profile not found"
INVALID_PHONE_NUMBER = "Invalid phone number format"
DUPLICATE_PHONE_NUMBER = "Phone number already exists"

# INVOICE ERRORS
INVOICE_NOT_FOUND = "Invoice not found"
INVOICE_INVALID_ID = "Invalid invoice ID provided"
INVALID_INVOICE_AMOUNT = "Invoice amount must be greater than zero"
INVALID_PLATFORM_FEE = "Platform fee cannot be negative"
INVALID_TAX_PERCENTAGE = "Tax percentage must be between 0 and 100"
INVOICE_ALREADY_PAID = "Invoice has already been paid"
INVOICE_CANNOT_DELETE = "Invoice cannot be deleted. It may have already been processed."
INVOICE_EMAIL_FAILED = "Failed to send invoice email"
INVALID_INVOICE_ITEMS = "Invoice must contain at least one item"
INVALID_CUSTOMER_EMAIL = "Invalid customer email address for invoice"
INVOICE_GENERATION_FAILED = "Failed to generate invoice. Please try again."
INVOICE_PAYMENT_ALREADY_RECORDED = "Payment has already been recorded for this invoice"
INVALID_ADDITIONAL_CHARGES = "Invalid additional charges provided"

# TRANSACTION ERRORS
INVALID_USER_ID = "Invalid user ID provided"
INVALID_USER = "User does not exist"
LOCAL_ORDER_NOT_PREPARED = "Local order is not prepared"
GATEWAY_CLIENT_NOT_CONFIGURED = "Payment gateway client is not configured"
INVALID_TRANSACTION_DATA = "Invalid or incomplete checkout data"
GATEWAY_VERIFICATION_NOT_SUPPORTED = "Payment gateway does not support signature verification"
REMOTE_ORDER_CREATION_FAILED = "Failed to create remote order with payment gateway"
TRANSACTION_VERIFICATION_FAILED = "Failed to verify transaction signature"
TRANSACTION_COMPLETION_FAILED = "Failed to complete transaction"
INVALID_PAYMENT_AMOUNT = "Payment amount must be greater than zero"

# STORAGE ERRORS
STORAGE_FILE_PATH_EMPTY = "File path cannot be empty"
STORAGE_FILE_NOT_FOUND = "File not found in storage"
STORAGE_FILE_ALREADY_EXISTS = "File already exists in storage"
STORAGE_UPLOAD_FAILED = "Failed to upload file to storage"
STORAGE_DOWNLOAD_FAILED = "Failed to download file from storage"
STORAGE_DELETE_FAILED = "Failed to delete file from storage"
STORAGE_LIST_FAILED = "Failed to list files in storage"
STORAGE_SEARCH_FAILED = "Failed to search files in storage"
STORAGE_COPY_FAILED = "Failed to copy file in storage"
STORAGE_MOVE_FAILED = "Failed to move file in storage"
STORAGE_GET_INFO_FAILED = "Failed to get file information from storage"
INVALID_STORAGE_TYPE = "Invalid storage type. Must be 'default' or 'staticfiles'"
STORAGE_OPERATION_FAILED = "Storage operation failed"

# MAILING

# SUBSCRIPTION ERRORS
SUBSCRIPTION_NOT_FOUND = "Subscription not found"
NO_ACTIVE_SUBSCRIPTION = "No active subscription found"
SUBSCRIPTION_TYPE_NOT_FOUND = "Subscription type not found"
DUPLICATE_SUBSCRIPTION_TYPE = "Subscription type with this name already exists"
INVALID_SUBSCRIPTION_DURATION = "Subscription duration must be greater than zero"
INVALID_SUBSCRIPTION_COST = "Subscription cost must be greater than zero"
SUBSCRIPTION_ALREADY_PURCHASED = "You have already purchased this subscription"
SUBSCRIPTION_EXPIRED = "Your subscription has expired"
SUBSCRIPTION_RENEWAL_FAILED = "Failed to renew subscription"

# SUBSCRIPTION ORDER ERRORS
ORDER_NOT_FOUND = "Order not found"
INVALID_ORDER_ID = "Invalid order ID provided"
ORDER_ALREADY_COMPLETED = "Order has already been completed"
ORDER_CANCELLED = "Order has been cancelled"
ORDER_PAYMENT_PENDING = "Payment for this order is still pending"
UNAUTHORIZED_ORDER_ACCESS = "You are not authorized to access this order"
ORDER_CREATION_FAILED = "Failed to create order. Please try again."

# PAYMENT ERRORS
PAYMENT_NOT_FOUND = "Payment not found"
INVALID_PAYMENT_ID = "Invalid payment ID provided"
PAYMENT_ALREADY_PROCESSED = "Payment has already been processed"
PAYMENT_FAILED = "Payment failed. Please try again."
INVALID_PAYMENT_SIGNATURE = "Invalid payment signature. Payment verification failed."
INCOMPLETE_PAYMENT_DATA = "Invalid or incomplete checkout data"
PAYMENT_VERIFICATION_FAILED = "Failed to verify payment. Please contact support."
PAYMENT_GATEWAY_ERROR = "Payment gateway error. Please try again later."
PAYMENT_TIMEOUT = "Payment request timed out. Please try again."
PAYMENT_CANCELLED_BY_USER = "Payment was cancelled by user"
PAYMENT_AMOUNT_MISMATCH = "Payment amount does not match order amount"

# RAZORPAY SPECIFIC ERRORS
RAZORPAY_ORDER_CREATION_FAILED = "Failed to create Razorpay order"
RAZORPAY_PAYMENT_VERIFICATION_FAILED = "Failed to verify Razorpay payment"
RAZORPAY_CLIENT_NOT_CONFIGURED = "Razorpay client is not configured"
RAZORPAY_INVALID_CREDENTIALS = "Invalid Razorpay credentials"

# BILL BREAKDOWN ERRORS
BILL_BREAKDOWN_FAILED = "Failed to calculate bill breakdown"
INVALID_CHARGE_CONFIGURATION = "Invalid charge configuration"
CHARGE_NOT_FOUND = "Charge configuration not found"
INVALID_CHARGE_AMOUNT_TYPE = "Invalid charge amount type. Must be '%' or 'INR'"
INVALID_CHARGE_AMOUNT = "Charge amount must be greater than zero"
