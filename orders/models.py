import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from products.models import Products

User = get_user_model()

class UniversalIdModel(models.Model):
    """Abstract model that gives every child model a unique UUID."""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        abstract = True

class TimeStampedModel(models.Model):
    """Abstract model that adds created_at and updated_at fields."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Order(UniversalIdModel, TimeStampedModel):
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        limit_choices_to={'role': 'customer'}
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        default='PENDING',
        choices=ORDER_STATUS_CHOICES
    )
    # Remove checkout foreign key to avoid circular import - we'll reference by checkout_request_id
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Additional useful fields
    delivery_address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Order {self.uuid} for {self.customer.email} ({self.status})"
    
    @property
    def order_number(self):
        """Human-readable order number"""
        return f"ORD-{str(self.uuid)[:8].upper()}"
    
    @property
    def total_items(self):
        """Total number of items in this order"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in ['PENDING', 'PAID', 'PROCESSING']

    class Meta:
        ordering = ['-created_at']

class OrderItem(models.Model):
    ITEM_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        Products, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendor_order_items',
        limit_choices_to={'role': 'vendor'}
    )
    status = models.CharField(
        max_length=20,
        default='PAID',
        choices=ITEM_STATUS_CHOICES
    )
    
    # Store product info in case product gets deleted
    product_name = models.CharField(max_length=255)
    product_image = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.quantity} x {self.product_name} in {self.order.order_number} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate subtotal
        if self.unit_price and self.quantity:
            self.subtotal = self.unit_price * self.quantity
        
        # Store product info
        if self.product and not self.product_name:
            self.product_name = self.product.title
            if self.product.image:
                self.product_image = self.product.image.url
        
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['product_name']