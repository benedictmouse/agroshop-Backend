# products/urls.py - Updated with public endpoints
from django.urls import path
from .views import (
    ProductListView,
    ProductCreateView,
    ProductDetailView,
    CategoryListCreateView,
    CategoryDetailView,
    PublicProductListView,  # NEW
    PublicProductDetailView,  # NEW
    )

urlpatterns = [
    # Public endpoints (no authentication required)
    path('public/', PublicProductListView.as_view(), name='public-products-list'),
    path('public/<int:pk>/', PublicProductDetailView.as_view(), name='public-product-detail'),
    
    # Vendor endpoints (authentication required)
    path('view/', ProductListView.as_view(), name='products-List'),
    path('create/', ProductCreateView.as_view(), name='create_product'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-details'),
    path('categories/', CategoryListCreateView.as_view(), name='categories-list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='Category-details'),
]