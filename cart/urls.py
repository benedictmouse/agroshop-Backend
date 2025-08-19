# from django.urls import path
# from .views import CartView, AddToCartView, RemoveFromCartView

# urlpatterns = [
#     path('cart/', CartView.as_view(), name='cart-detail'),
#     path('cart/add/', AddToCartView.as_view(), name='cart-add'),
#     path('cart/remove/<int:product_id>/', RemoveFromCartView.as_view(), name='cart-remove'),
# ]


# urls.py - Cart URLs
from django.urls import path
from .views import (
    CartView,
    AddToCartView,
    CartItemDetailView,
    ClearCartView,
    OrderHistoryView,
)

urlpatterns = [
    # Cart endpoints
    path('cart/', CartView.as_view(), name='cart-detail'),                    # GET /cart/
    path('cart/add/', AddToCartView.as_view(), name='add-to-cart'),          # POST /cart/add/
    path('item/<int:item_id>/', CartItemDetailView.as_view(), name='cart-item-detail'),  # PUT, DELETE /cart/item/5/
    path('clear/', ClearCartView.as_view(), name='clear-cart'),         # DELETE /cart/clear/
    path('orders/history/', OrderHistoryView.as_view(), name='order-history'),
]