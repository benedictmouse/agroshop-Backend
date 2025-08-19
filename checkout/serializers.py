from rest_framework import serializers
from .models import Checkout

class CheckoutSerializer(serializers.ModelSerializer):
    cart_total = serializers.DecimalField(source='cart.total_price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Checkout
        fields = [
            'uuid', 'cart', 'cart_total', 'phone', 'amount', 'status', 
            'receipt', 'error_message', 'attempt_number', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'uuid', 'status', 'receipt', 'error_message', 'attempt_number', 
            'is_active', 'created_at', 'updated_at', 'cart_total'
        ]