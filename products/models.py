from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Products(models.Model):
    title = models.CharField(max_length = 255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveBigIntegerField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    image = models.ImageField(upload_to='products/productimage/', blank=True, null=True)
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', limit_choices_to={'role': 'vendor'})

    def __str__(self):
        return self.title


