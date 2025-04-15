# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, CartItem, Order
from django.db.models import Sum
from .peach import api as peach_api
from .peach import utils as peach_utils

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
        
        # Extract user data from the request
        user_data = peach_utils.extract_user_data_from_request(request)
        
        # Create checkout with Peach Payments
        return_url = request.build_absolute_uri('/payment-result/')
        
        try:
            response_data = peach_api.create_checkout(order, user_data, return_url)
            
            if response_data and response_data.get('result', {}).get('code') == '000.200.100':
                # Successfully created checkout, store checkout ID
                checkout_id = response_data.get('id')
                
                # Store the checkout ID with the order
                order.payment_id = checkout_id
                order.save()
                
                # Get payment widget URL
                payment_url = peach_api.get_widget_url(checkout_id)
                
                return render(request, 'payment.html', {
                    'payment_url': payment_url,
                    'checkout_id': checkout_id,
                    'order': order
                })
            else:
                # Handle error from Peach Payments
                error_message = response_data.get('result', {}).get('description', 'Payment initialization failed') if response_data else 'Failed to connect to payment gateway'
                return render(request, 'checkout_error.html', {'error': error_message})
        except Exception as e:
            # Handle exceptions
            return render(request, 'checkout_error.html', {'error': str(e)})
    
    return render(request, 'checkout.html', {'cart_items': cart_items, 'total': total})

@login_required
def payment_result(request):
    checkout_id = request.GET.get('id')
    resource_path = request.GET.get('resourcePath')
    
    if not checkout_id or not resource_path:
        return render(request, 'checkout_error.html', {'error': 'Invalid payment response'})
    
    # Find the order by payment_id
    try:
        order = Order.objects.get(payment_id=checkout_id)
    except Order.DoesNotExist:
        return render(request, 'checkout_error.html', {'error': 'Order not found'})
    
    try:
        # Query Peach Payments for status
        response_data = peach_api.get_payment_status(resource_path)
        
        if response_data:
            payment_result = response_data.get('result', {})
            result_code = payment_result.get('code')
            
            if peach_utils.is_payment_successful(result_code):
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
            # Handle API error
            order.delete()  # Delete the order since payment verification failed
            return render(request, 'checkout_error.html', {'error': 'Failed to verify payment status'})
    except Exception as e:
        # Handle exceptions
        return render(request, 'checkout_error.html', {'error': str(e)})