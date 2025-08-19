from django.urls import path
from .views import InitiateCheckoutView, MpesaCallbackView, CheckoutHistoryView

urlpatterns = [
    path('initiate/', InitiateCheckoutView.as_view(), name='initiate-checkout'),
    path('mpesa-callback/', MpesaCallbackView.as_view(), name='mpesa-callback'),
    path('history/<int:cart_id>/', CheckoutHistoryView.as_view(), name='checkout-history'),
]