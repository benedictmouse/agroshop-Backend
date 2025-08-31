# products/serializers.py - KEEP YOUR EXISTING CODE, JUST MODIFY to_representation
from rest_framework import serializers
from .models import Products, Category
from django.contrib.auth import get_user_model

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class ProductSerializer(serializers.ModelSerializer):
    category = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = Products
        fields = ['id', 'title', 'description', 'price', 'stock', 'category', 'image']  # Keep same fields
        extra_kwargs = {
            'image': {'required': False, 'allow_null': True}
        }

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("The price should be a positive number")
        return value

    def validate_stock(self, value):
        if value < 0:  
            raise serializers.ValidationError("The stock should not be negative")
        return value

    def create(self, validated_data):
        category_name = validated_data.pop('category', None)
        category = None
        if category_name:
            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={'description': ''}
            )
        validated_data['category'] = category
        return super().create(validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['vendor'] = instance.vendor.id if instance.vendor else None
        
        # MODIFY THIS PART - make 'image' field return the Cloudinary URL
        if instance.image:
            representation['image'] = instance.image.url
        else:
            representation['image'] = None
        
        return representation