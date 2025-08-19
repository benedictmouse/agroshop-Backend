# cart/serializer.py
from rest_framework import serializers
from .models import Cart, CartItem

class CartItemSerializer(serializers.ModelSerializer):
    # Read-only fields that fetch from product
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    product_name = serializers.CharField(source='product.title', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    
    # Add the full product data for frontend
    product = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'product_image', 'quantity', 'unit_price', 'total_price', 'added_at']
        read_only_fields = ['id', 'added_at', 'unit_price', 'total_price']

    def get_product(self, obj):
        """Return complete product data"""
        return {
            'id': obj.product.id,
            'title': obj.product.title,
            'price': str(obj.product.price),
            'image': obj.product.image.url if obj.product.image else None,
            'color': getattr(obj.product, 'color', None),
            'size': getattr(obj.product, 'size', None),
            'stock': getattr(obj.product, 'stock', 0),
        }

    def validate_price(self, value):
        """Validate price from product"""
        if value is None:
            return 0.00
        if value <= 0:
            raise serializers.ValidationError("Product must have a valid price")
        return value

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value

    def validate_product(self, value):
        # Check if product exists and has valid price
        if not value.price or value.price <= 0:
            raise serializers.ValidationError("Product must have a valid price")
        if hasattr(value, 'stock') and value.stock <= 0:
            raise serializers.ValidationError("Product is out of stock")
        return value

    def validate(self, attrs):
        product = attrs.get('product')
        quantity = attrs.get('quantity', 1)
        
        if product and hasattr(product, 'stock') and quantity > product.stock:
            raise serializers.ValidationError(
                f"Only {product.stock} items available in stock"
            )
        return attrs

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_amount', 'total_items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())