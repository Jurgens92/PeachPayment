# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, CartItem, Order
from django.db.models import Sum
import requests
import json

def dashboard(request):
    products = Product.objects.all()[:3]  # Get only 3 products
    return render(request, 'dashboard.html', {'products': products})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        
    return redirect('cart')

@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.get_total() for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    return redirect('cart')


@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        return redirect('cart')
        
    total = sum(item.get_total() for item in cart_items)
    
    if request.method == 'POST':
        # Create order first
        order = Order.objects.create(
            user=request.user,
            total_amount=total,
            payment_id=''  # Will update after payment
        )
        order.items.set(cart_items)
        
        # Prepare data for Peach Payments
        # For test environment
        url = "https://test.oppwa.com/v1/checkouts"
        
        # You'll need to get these credentials from Peach Payments
        entity_id = "YOUR_ENTITY_ID"  # Replace with your test entity ID
        access_token = "YOUR_ACCESS_TOKEN"  # Replace with your test token
        
        # Prepare the request data
        data = {
            "entityId": entity_id,
            "amount": str(total),
            "currency": "ZAR",
            "paymentType": "DB",  # Direct Debit/Sale
            "merchantTransactionId": str(order.id),
            "customer.email": request.user.email,
            "billing.street1": request.POST.get('address', ''),
            "billing.city": request.POST.get('city', ''),
            "billing.state": request.POST.get('province', ''),
            "billing.postcode": request.POST.get('postal_code', ''),
            "billing.country": "ZA",  # South Africa
            "customParameters[SHOPPER_orderNumber]": str(order.id),
            "customParameters[SHOPPER_returnUrl]": request.build_absolute_uri('/payment-result/')
        }
        
        # Make the request to create a checkout ID
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            response = requests.post(url, data=data, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get('result', {}).get('code') == '000.200.100':
                    # Successfully created checkout, store checkout ID
                    checkout_id = response_data.get('id')
                    
                    # Store the checkout ID with the order
                    order.payment_id = checkout_id
                    order.save()
                    
                    # Redirect to the payment page
                    payment_url = f"https://test.oppwa.com/v1/paymentWidgets.js?checkoutId={checkout_id}"
                    return render(request, 'payment.html', {
                        'payment_url': payment_url,
                        'checkout_id': checkout_id,
                        'order': order
                    })
                else:
                    # Handle error from Peach Payments
                    error_message = response_data.get('result', {}).get('description', 'Payment initialization failed')
                    return render(request, 'checkout_error.html', {'error': error_message})
            else:
                # Handle HTTP error
                return render(request, 'checkout_error.html', {'error': 'Failed to connect to payment gateway'})
                
        except Exception as e:
            # Handle exceptions
            return render(request, 'checkout_error.html', {'error': str(e)})
    
    return render(request, 'checkout.html', {'cart_items': cart_items, 'total': total})
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.get_total() for item in cart_items)
    
    if request.method == 'POST':
        # Peach Payments integration here
        # This is a simplified example and would need proper implementation
        url = "https://testsecure.peachpayments.com/checkout"
        payload = {
            "authentication.entityId": "YOUR_ENTITY_ID",  # Replace with actual ID
            "amount": str(total),
            "currency": "ZAR",
            "paymentType": "DB",
            # Add more required fields from the Peach Payment API
        }
        
        # In a real implementation, you would handle the response properly
        # For now, we'll just simulate a successful order
        
        order = Order.objects.create(
            user=request.user,
            total_amount=total
        )
        order.items.set(cart_items)
        
        # Clear the cart
        cart_items.delete()
        
        return render(request, 'checkout_success.html', {'order': order})
    
    return render(request, 'checkout.html', {'cart_items': cart_items, 'total': total})


@login_required
def payment_result(request):
    checkout_id = request.GET.get('id')
    resourcePath = request.GET.get('resourcePath')
    
    if not checkout_id or not resourcePath:
        return render(request, 'checkout_error.html', {'error': 'Invalid payment response'})
    
    # Find the order by payment_id
    try:
        order = Order.objects.get(payment_id=checkout_id)
    except Order.DoesNotExist:
        return render(request, 'checkout_error.html', {'error': 'Order not found'})
    
    # Query Peach Payments for status
    url = f"https://test.oppwa.com/v1{resourcePath}"
    access_token = "YOUR_ACCESS_TOKEN"  # Replace with your test token
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            response_data = response.json()
            payment_result = response_data.get('result', {})
            result_code = payment_result.get('code')
            
            if result_code.startswith('000.'):
                # Payment was successful
                # Clear the user's cart
                CartItem.objects.filter(user=request.user).delete()
                
                return render(request, 'checkout_success.html', {'order': order})
            else:
                # Payment failed
                error_message = payment_result.get('description', 'Payment failed')
                order.delete()  # Delete the order since payment failed
                return render(request, 'checkout_error.html', {'error': error_message})
        else:
            # Handle HTTP error
            order.delete()  # Delete the order since payment verification failed
            return render(request, 'checkout_error.html', {'error': 'Failed to verify payment status'})
            
    except Exception as e:
        # Handle exceptions
        return render(request, 'checkout_error.html', {'error': str(e)})