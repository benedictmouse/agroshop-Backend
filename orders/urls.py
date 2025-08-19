from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Customer order management
    path('orders/', views.CustomerOrderListView.as_view(), name='customer-order-list'),
    path('orders/<uuid:order_uuid>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/<uuid:order_uuid>/cancel/', views.CancelOrderView.as_view(), name='cancel-order'),
    
    # Vendor order item management
    path('vendor/order-items/', views.VendorOrderItemsView.as_view(), name='vendor-order-items'),
    path('vendor/order-items/<int:item_id>/status/', views.UpdateOrderItemStatusView.as_view(), name='update-order-item-status'),
    
    # Utility endpoints
    path('status-choices/', views.OrderStatusChoicesView.as_view(), name='order-status-choices'),
]