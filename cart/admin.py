# admin.py - Simple fixed version
from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    readonly_fields = ('total_price',)  # Changed from 'subtotal' to 'total_price'

class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_email', 'created_at', 'total_amount')  # Removed non-existent fields
    search_fields = ('user__email',)
    # list_filter = ('created_at',)  # Removed non-existent fields
    inlines = [CartItemInline]
    list_per_page = 20

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'total_price')  # Changed from 'subtotal' to 'total_price'
    search_fields = ('cart__user__email', 'product__title')
    list_per_page = 20

admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)