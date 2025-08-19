import base64
from datetime import datetime
import requests
import json
from django.conf import settings
from .models import Checkout, MpesaBody

def get_access_token():
    """Generate MPESA OAuth access token."""
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    api_url = settings.MPESA_ACCESS_TOKEN_URL
    response = requests.get(api_url, auth=(consumer_key, consumer_secret))
    return response.json()['access_token']

def generate_mpesa_password(shortcode, passkey):
    """Generate MPESA password for STK Push."""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(data.encode()).decode(), timestamp

def initiate_stk_push(phone, amount, account_reference, transaction_desc, callback_url):
    """Initiate MPESA Express (STK Push) transaction."""
    access_token = get_access_token()
    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    password, timestamp = generate_mpesa_password(shortcode, passkey)

    payload = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(amount),
        'PartyA': phone,
        'PartyB': shortcode,
        'PhoneNumber': phone,
        'CallBackURL': callback_url,
        'AccountReference': account_reference,
        'TransactionDesc': transaction_desc
    }
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    response = requests.post(settings.MPESA_STK_PUSH_URL, json=payload, headers=headers)
    return response.json()

def process_stk_callback(data):
    """Process MPESA Express callback and create Order on success."""
    checkout_request_id = data['Body']['stkCallback']['CheckoutRequestID']
    result_code = data['Body']['stkCallback']['ResultCode']
    result_desc = data['Body']['stkCallback']['ResultDesc']

    try:
        checkout = Checkout.objects.get(checkout_request_id=checkout_request_id)
    except Checkout.DoesNotExist:
        # Log error if needed, but return accepted to M-Pesa
        return {'ResultCode': 0, 'ResultDesc': 'Accepted'}

    # Create MpesaBody record
    MpesaBody.objects.create(
        checkout=checkout,
        body=data,
        result_code=result_code,
        result_desc=result_desc
    )

    if int(result_code) == 0:  # Success
        checkout.status = 'SUCCESS'
        metadata = data['Body']['stkCallback']['CallbackMetadata']['Item']
        for item in metadata:
            if item['Name'] == 'MpesaReceiptNumber':
                checkout.receipt = item['Value']
                break

        # Create Order from Cart on success
        cart = checkout.cart
        
        # Import here to avoid circular imports
        from orders.models import Order, OrderItem
        
        # Check if order already exists for this checkout to avoid duplicates
        existing_order = Order.objects.filter(checkout_request_id=checkout_request_id).first()
        if not existing_order:
            # Also check if any successful order exists for this cart
            cart_order = Order.objects.filter(
                customer=cart.user,
                total_price=checkout.amount
            ).first()
            
            if not cart_order:
                # Create the Order
                order = Order.objects.create(
                    customer=cart.user,
                    total_price=checkout.amount,
                    status='PAID',
                    checkout_request_id=checkout_request_id,
                    phone_number=checkout.phone
                )
                
                # Create OrderItems from CartItems
                for cart_item in cart.items.all():
                    # Get vendor from product if it exists
                    vendor = None
                    if hasattr(cart_item.product, 'vendor'):
                        vendor = cart_item.product.vendor
                    elif hasattr(cart_item.product, 'user'):
                        vendor = cart_item.product.user
                        
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        unit_price=cart_item.unit_price,
                        subtotal=cart_item.total_price,
                        vendor=vendor,
                        status='PAID',
                        product_name=cart_item.product.title,
                        product_image=cart_item.product.image.url if cart_item.product.image else None
                    )
                
                # Mark Cart as completed
                if hasattr(cart, 'is_ordered') and hasattr(cart, 'is_paid'):
                    cart.is_ordered = True
                    cart.is_paid = True
                    cart.save()

    else:
        checkout.status = 'FAILED'
        checkout.error_message = result_desc

    checkout.save()
    return {'ResultCode': 0, 'ResultDesc': 'Accepted'}