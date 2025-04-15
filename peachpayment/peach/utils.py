# peachpayment/peach/utils.py

def is_payment_successful(result_code):
    """
    Check if the payment was successful based on result code
    
    Args:
        result_code: Result code from Peach Payments
        
    Returns:
        bool: True if payment was successful, False otherwise
    """
    return result_code and result_code.startswith('000.')

def extract_user_data_from_request(request):
    """
    Extract user data from a POST request
    
    Args:
        request: Django request object
        
    Returns:
        dict: User data from the request
    """
    return {
        'email': request.user.email,
        'address': request.POST.get('address', ''),
        'city': request.POST.get('city', ''),
        'province': request.POST.get('province', ''),
        'postal_code': request.POST.get('postal_code', ''),
    }