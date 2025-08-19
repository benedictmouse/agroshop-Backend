# cart/models.py - UPDATED VERSION
from django.db import models
from django.contrib.auth import get_user_model
from products.models import Products

User = get_user_model()

class Cart(models.Model):
    # MAJOR CHANGE: OneToOneField to ForeignKey to allow multiple carts per user
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # NEW FIELDS - These are what you're adding
    is_ordered = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    
    class Meta:
        # Add constraint to ensure only one active cart per user
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_ordered=False, is_paid=False),
                name='one_active_cart_per_user'
            )
        ]

    def __str__(self):
        status = "Active"
        if self.is_paid and self.is_ordered:
            status = "Completed"
        elif self.is_ordered:
            status = "Ordered"
        
        return f"Cart for {self.user.email} - {status}"

    @property
    def total_amount(self):
        """Calculate total cart amount"""
        total = sum(item.total_price for item in self.items.all())
        return total or 0.00

    @property
    def total_price(self):
        """Alias for total_amount to match your checkout code"""
        return self.total_amount

# CartItem remains the same
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

    @property
    def unit_price(self):
        return self.product.price or 0.00

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    @property
    def subtotal(self):
        """Alias for total_price to match your frontend code"""
        return self.total_price