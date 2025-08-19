import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from cart.models import Cart
from .models import Checkout
from .serializers import CheckoutSerializer
from .utils import initiate_stk_push, process_stk_callback


class InitiateCheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if request.user.role != 'customer':
            return Response({'error': 'Only customers can initiate checkout.'}, status=status.HTTP_403_FORBIDDEN)

        cart_id = request.data.get('cart_id')
        phone = request.data.get('phone')

        if not phone:
            return Response({'error': 'Phone number is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart = Cart.objects.get(id=cart_id, user=request.user, is_ordered=False, is_paid=False)
        except Cart.DoesNotExist:
            return Response({'error': 'Invalid or already processed cart.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if there's already a successful checkout for this cart
        successful_checkout = Checkout.objects.filter(cart=cart, status='SUCCESS').first()
        if successful_checkout:
            return Response({
                'error': 'This cart has already been successfully paid for.',
                'existing_checkout': CheckoutSerializer(successful_checkout).data
            }, status=status.HTTP_400_BAD_REQUEST)

        if cart.total_price <= 0:
            return Response({'error': 'Cart is empty or total price is zero.'}, status=status.HTTP_400_BAD_REQUEST)

        amount = cart.total_price
        account_reference = f'Cart-{cart.id}'
        transaction_desc = 'Payment for e-commerce order'
        callback_url = settings.MPESA_CALLBACK_URL

        response = initiate_stk_push(phone, amount, account_reference, transaction_desc, callback_url)

        if 'ResponseCode' in response and response['ResponseCode'] == '0':
            # SOLUTION 2: Always create a new checkout record
            checkout = Checkout.objects.create(
                cart=cart,
                phone=phone,
                amount=amount,
                checkout_request_id=response['CheckoutRequestID']
            )

            return Response({
                'message': 'STK Push initiated successfully. Please check your phone.',
                'checkout': CheckoutSerializer(checkout).data
            }, status=status.HTTP_200_OK)
        else:
            error = response.get('errorMessage', 'Failed to initiate STK Push.')
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class MpesaCallbackView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON data.'}, status=status.HTTP_400_BAD_REQUEST)

        process_stk_callback(data)
        return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'}, status=status.HTTP_200_OK)


class CheckoutHistoryView(APIView):
    """View all checkout attempts for a cart"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, cart_id):
        if request.user.role != 'customer':
            return Response({'error': 'Only customers can view checkout history.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            cart = Cart.objects.get(id=cart_id, user=request.user)
            checkouts = Checkout.objects.filter(cart=cart).order_by('-created_at')
            serializer = CheckoutSerializer(checkouts, many=True)
            
            return Response({
                'cart_id': cart_id,
                'checkout_history': serializer.data,
                'total_attempts': checkouts.count(),
                'successful_checkouts': checkouts.filter(status='SUCCESS').count(),
                'failed_checkouts': checkouts.filter(status='FAILED').count(),
                'pending_checkouts': checkouts.filter(status='PENDING').count()
            })
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found.'}, status=status.HTTP_404_NOT_FOUND)
