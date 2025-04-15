# peachpayment/peach/api.py
import requests
from . import config

def create_checkout(order, user_data, return_url):
    """
    Create a checkout session with Peach Payments
    
    Args:
        order: The Order model instance
        user_data: Dictionary with user billing details
        return_url: URL to return to after payment
        
    Returns:
        dict: Response from Peach Payments API
    """
    url = config.TEST_CHECKOUT_URL
    
    data = {
        "entityId": config.ENTITY_ID,
        "amount": str(order.total_amount),
        "currency": config.DEFAULT_CURRENCY,
        "paymentType": config.DEFAULT_PAYMENT_TYPE,
        "merchantTransactionId": str(order.id),
        "customer.email": user_data.get('email', ''),
        "billing.street1": user_data.get('address', ''),
        "billing.city": user_data.get('city', ''),
        "billing.state": user_data.get('province', ''),
        "billing.postcode": user_data.get('postal_code', ''),
        "billing.country": "ZA",  # South Africa
        "customParameters[SHOPPER_orderNumber]": str(order.id),
        "customParameters[SHOPPER_returnUrl]": return_url
    }
    
    headers = {
        'Authorization': f'Bearer {config.ACCESS_TOKEN}'
    }
    
    response = requests.post(url, data=data, headers=headers)
    return response.json() if response.status_code == 200 else None

def get_payment_status(resource_path):
    """
    Get the status of a payment from Peach Payments
    
    Args:
        resource_path: Resource path from Peach Payments
        
    Returns:
        dict: Response from Peach Payments API
    """
    url = f"{config.TEST_BASE_URL}{resource_path}"
    
    headers = {
        'Authorization': f'Bearer {config.ACCESS_TOKEN}'
    }
    
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

def get_widget_url(checkout_id):
    """
    Get the URL for the payment widget JS
    
    Args:
        checkout_id: Checkout ID from Peach Payments
        
    Returns:
        str: URL for the payment widget JS
    """
    return f"{config.TEST_WIDGET_JS_URL}?checkoutId={checkout_id}"