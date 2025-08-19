from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    vendor_name = serializers.CharField(source='vendor.email', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_title', 'product_name', 'product_image',
            'quantity', 'unit_price', 'subtotal', 'vendor', 'vendor_name', 
            'status'
        ]
        read_only_fields = ['id', 'subtotal', 'product_title', 'vendor_name']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    order_number = serializers.CharField(read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    can_be_cancelled = serializers.BooleanField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'uuid', 'order_number', 'customer', 'customer_email', 
            'total_price', 'total_items', 'status', 'checkout_request_id',
            'delivery_address', 'phone_number', 'notes', 'items',
            'can_be_cancelled', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'uuid', 'order_number', 'customer_email', 'total_items', 
            'can_be_cancelled', 'created_at', 'updated_at'
        ]

class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'delivery_address', 'phone_number', 'notes'
        ]
