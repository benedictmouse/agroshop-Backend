from django.contrib import admin
from .models import Products, Category

class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'price', 'stock', 'category', 'vendor')
    search_fields = ('title', 'description', 'category__name')
    list_filter = ('category', 'vendor')
    list_per_page = 20

    # def vendor_email(self, obj):
    #     return obj.vendor.email
    # vendor_email.short_description = 'Vendor Email'

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    list_per_page = 20

admin.site.register(Products, ProductAdmin)
admin.site.register(Category, CategoryAdmin)