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