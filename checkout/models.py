import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from cart.models import Cart

User = get_user_model()

class UniversalIdModel(models.Model):
    """
    Abstract model that gives every child model a unique UUID.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        abstract = True

class TimeStampedModel(models.Model):
    """
    Abstract model that adds created_at and updated_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Checkout(UniversalIdModel, TimeStampedModel):
    # SOLUTION 2: Change to ForeignKey to allow multiple checkout attempts per cart
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='checkouts')
    phone = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    status = models.CharField(
        max_length=20,
        default='PENDING',
        choices=(('PENDING', 'Pending'), ('SUCCESS', 'Success'), ('FAILED', 'Failed'))
    )
    receipt = models.CharField(max_length=100, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Additional fields for tracking
    attempt_number = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)  # Mark the current active checkout

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cart', 'status']),
            models.Index(fields=['checkout_request_id']),
        ]

    def save(self, *args, **kwargs):
        if not self.pk:  # New checkout
            # Set attempt number
            last_checkout = Checkout.objects.filter(cart=self.cart).order_by('-attempt_number').first()
            self.attempt_number = (last_checkout.attempt_number + 1) if last_checkout else 1
            
            # Deactivate all previous checkouts for this cart
            Checkout.objects.filter(cart=self.cart, is_active=True).update(is_active=False)
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Checkout {self.uuid} for Cart {self.cart.id} - Attempt #{self.attempt_number} ({self.status})"

class MpesaBody(UniversalIdModel, TimeStampedModel):
    checkout = models.ForeignKey(Checkout, on_delete=models.CASCADE, related_name='mpesa_bodies')
    body = models.JSONField()
    result_code = models.CharField(max_length=10)
    result_desc = models.TextField()

    def __str__(self):
        return f"MpesaBody for Checkout {self.checkout.uuid} (Code: {self.result_code})"
