# peachpayment/peach/config.py

# Test environment URLs
TEST_BASE_URL = "https://test.oppwa.com/v1"
TEST_CHECKOUT_URL = f"{TEST_BASE_URL}/checkouts"
TEST_WIDGET_JS_URL = f"{TEST_BASE_URL}/paymentWidgets.js"

# Production environment URLs (for when you're ready)
PROD_BASE_URL = "https://oppwa.com/v1"
PROD_CHECKOUT_URL = f"{PROD_BASE_URL}/checkouts"
PROD_WIDGET_JS_URL = f"{PROD_BASE_URL}/paymentWidgets.js"

# Credentials
ENTITY_ID = "YOUR_ENTITY_ID"  # Replace with your entity ID
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"  # Replace with your access token

# Default settings
DEFAULT_CURRENCY = "ZAR"
DEFAULT_PAYMENT_TYPE = "DB"  # Direct Debit/Sale