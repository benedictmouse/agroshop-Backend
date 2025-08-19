# orders/views.py
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer, OrderCreateSerializer

class IsCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                hasattr(request.user, 'role') and request.user.role == 'customer')

class IsVendor(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                hasattr(request.user, 'role') and request.user.role == 'vendor')

class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

class CustomerOrderListView(APIView):
    """Customer can view their order history"""
    permission_classes = [IsCustomer]
    pagination_class = OrderPagination

    def get(self, request):
        try:
            orders = Order.objects.filter(customer=request.user)
            
            # Filter by status if provided
            status_filter = request.query_params.get('status')
            if status_filter:
                orders = orders.filter(status=status_filter)
            
            # Search by order number
            search = request.query_params.get('search')
            if search:
                orders = orders.filter(
                    Q(uuid__icontains=search) | 
                    Q(items__product_name__icontains=search)
                ).distinct()
            
            # Pagination
            paginator = OrderPagination()
            paginated_orders = paginator.paginate_queryset(orders, request)
            
            serializer = OrderSerializer(paginated_orders, many=True)
            
            # Summary stats
            total_orders = orders.count()
            total_spent = orders.aggregate(total=Sum('total_price'))['total'] or 0
            
            response_data = {
                'orders': serializer.data,
                'summary': {
                    'total_orders': total_orders,
                    'total_spent': float(total_spent),
                    'pending_orders': orders.filter(status='PENDING').count(),
                    'shipped_orders': orders.filter(status='SHIPPED').count(),
                    'delivered_orders': orders.filter(status='DELIVERED').count(),
                }
            }
            
            return paginator.get_paginated_response(response_data)
            
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch orders'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class OrderDetailView(APIView):
    """View specific order details"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_uuid):
        try:
            if request.user.role == 'customer':
                order = get_object_or_404(Order, uuid=order_uuid, customer=request.user)
            elif request.user.role == 'vendor':
                # Vendor can see orders containing their products
                order = get_object_or_404(
                    Order.objects.filter(items__vendor=request.user).distinct(),
                    uuid=order_uuid
                )
            else:
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
            
            serializer = OrderSerializer(order)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': 'Order not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class CancelOrderView(APIView):
    """Customer can cancel their order if eligible"""
    permission_classes = [IsCustomer]

    def post(self, request, order_uuid):
        try:
            order = get_object_or_404(Order, uuid=order_uuid, customer=request.user)
            
            if not order.can_be_cancelled:
                return Response(
                    {'error': f'Order cannot be cancelled. Current status: {order.status}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            reason = request.data.get('reason', '')
            
            # Update order and all items
            order.status = 'CANCELLED'
            order.notes = f"Cancelled by customer. Reason: {reason}"
            order.save()
            
            # Cancel all order items
            order.items.update(status='CANCELLED')
            
            return Response({
                'message': 'Order cancelled successfully',
                'order': OrderSerializer(order).data
            })
            
        except Exception as e:
            return Response(
                {'error': 'Failed to cancel order'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VendorOrderItemsView(APIView):
    """Vendor can view and update their order items"""
    permission_classes = [IsVendor]
    pagination_class = OrderPagination

    def get(self, request):
        try:
            order_items = OrderItem.objects.filter(vendor=request.user).select_related('order', 'product')
            
            # Filter by status
            status_filter = request.query_params.get('status')
            if status_filter:
                order_items = order_items.filter(status=status_filter)
            
            # Pagination
            paginator = OrderPagination()
            paginated_items = paginator.paginate_queryset(order_items, request)
            
            serializer = OrderItemSerializer(paginated_items, many=True)
            
            # Summary stats
            total_items = order_items.count()
            revenue = order_items.aggregate(total=Sum('subtotal'))['total'] or 0
            
            response_data = {
                'order_items': serializer.data,
                'summary': {
                    'total_items': total_items,
                    'total_revenue': float(revenue),
                    'pending_items': order_items.filter(status='PAID').count(),
                    'processing_items': order_items.filter(status='PROCESSING').count(),
                    'shipped_items': order_items.filter(status='SHIPPED').count(),
                    'delivered_items': order_items.filter(status='DELIVERED').count(),
                }
            }
            
            return paginator.get_paginated_response(response_data)
            
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch order items'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UpdateOrderItemStatusView(APIView):
    """Vendor updates order item status"""
    permission_classes = [IsVendor]

    def patch(self, request, item_id):
        try:
            order_item = get_object_or_404(OrderItem, id=item_id, vendor=request.user)
            new_status = request.data.get('status')
            
            if not new_status:
                return Response(
                    {'error': 'Status is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate status transition
            valid_statuses = ['PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED']
            if new_status not in valid_statuses:
                return Response(
                    {'error': f'Invalid status. Must be one of: {valid_statuses}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update item status
            order_item.status = new_status
            order_item.save()
            
            # Update order status based on all items
            order = order_item.order
            all_items = order.items.all()
            
            # Logic to update overall order status
            if all(item.status == 'DELIVERED' for item in all_items):
                order.status = 'DELIVERED'
            elif all(item.status == 'CANCELLED' for item in all_items):
                order.status = 'CANCELLED'
            elif any(item.status == 'SHIPPED' for item in all_items):
                order.status = 'SHIPPED'
            elif any(item.status == 'PROCESSING' for item in all_items):
                order.status = 'PROCESSING'
            
            order.save()
            
            return Response({
                'message': f'Order item status updated to {new_status}',
                'order_item': OrderItemSerializer(order_item).data,
                'order_status': order.status
            })
                
        except Exception as e:
            return Response(
                {'error': 'Failed to update order item'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class OrderStatusChoicesView(APIView):
    """Get available order status choices"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'order_statuses': dict(Order.ORDER_STATUS_CHOICES),
            'item_statuses': dict(OrderItem.ITEM_STATUS_CHOICES)
        })
