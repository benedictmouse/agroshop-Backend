# cart/views.py - COMPLETELY REWRITTEN
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import Http404
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from .serializer import CartSerializer, CartItemSerializer
from products.models import Products

class IsCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'role') and request.user.role == 'customer'

class CartView(APIView):
    """View user's ACTIVE cart"""
    permission_classes = [IsCustomer]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        """Get user's active cart with all items"""
        try:
            # MAJOR CHANGE: Get only active cart (not ordered/paid)
            cart, created = Cart.objects.get_or_create(
                user=request.user,
                is_ordered=False,
                is_paid=False
            )
            serializer = CartSerializer(cart)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Failed to fetch cart"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AddToCartView(APIView):
    """Add item to ACTIVE cart only"""
    permission_classes = [IsCustomer]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            product_id = request.data.get('product_id')
            quantity = int(request.data.get('quantity', 1))

            if not product_id:
                return Response(
                    {'error': 'Product ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # MAJOR CHANGE: Get or create ACTIVE cart only
            cart, created = Cart.objects.get_or_create(
                user=request.user,
                is_ordered=False,
                is_paid=False
            )
            
            try:
                product = Products.objects.get(id=product_id)
            except Products.DoesNotExist:
                return Response(
                    {'error': 'Product not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if not product.price or product.price <= 0:
                return Response(
                    {'error': 'Product must have a valid price'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            serializer = CartItemSerializer(cart_item)
            
            return Response({
                'message': 'Item added to cart successfully',
                'cart_item': serializer.data
            }, status=status.HTTP_201_CREATED)

        except ValueError:
            return Response(
                {'error': 'Invalid quantity'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'An unexpected error occurred while adding to cart'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CartItemDetailView(APIView):
    """Update or remove specific cart item from ACTIVE cart only"""
    permission_classes = [IsCustomer]
    authentication_classes = [JWTAuthentication]

    def get_object(self, request, item_id):
        """Get cart item from ACTIVE cart only"""
        try:
            return CartItem.objects.get(
                id=item_id, 
                cart__user=request.user,
                cart__is_ordered=False,  # NEW: Only from active carts
                cart__is_paid=False      # NEW: Only from active carts
            )
        except CartItem.DoesNotExist:
            raise Http404("Cart item not found in active cart")

    def put(self, request, item_id):
        """Update cart item quantity in active cart only"""
        try:
            cart_item = self.get_object(request, item_id)
            quantity = int(request.data.get('quantity', 1))
            
            if quantity <= 0:
                return Response(
                    {'error': 'Quantity must be greater than 0. Use DELETE to remove item.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cart_item.quantity = quantity
            cart_item.save()
            
            serializer = CartItemSerializer(cart_item)
            
            return Response({
                'message': 'Cart item updated successfully',
                'cart_item': serializer.data
            }, status=status.HTTP_200_OK)
            
        except ValueError:
            return Response(
                {'error': 'Invalid quantity'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Http404 as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, item_id):
        """Remove item from active cart only"""
        try:
            cart_item = self.get_object(request, item_id)
            product_title = cart_item.product.title
            
            action = request.data.get('action', 'remove_all')
            
            if action == 'remove_all' or cart_item.quantity == 1:
                cart_item.delete()
                return Response(
                    {'message': f'Item "{product_title}" removed from cart completely'}, 
                    status=status.HTTP_200_OK
                )
            else:
                cart_item.quantity -= 1
                cart_item.save()
                
                serializer = CartItemSerializer(cart_item)
                return Response({
                    'message': f'Removed 1 quantity of "{product_title}". {cart_item.quantity} remaining.',
                    'cart_item': serializer.data
                }, status=status.HTTP_200_OK)
                
        except Http404 as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_404_NOT_FOUND
            )

class ClearCartView(APIView):
    """Clear all items from user's ACTIVE cart"""
    permission_classes = [IsCustomer]
    authentication_classes = [JWTAuthentication]

    def delete(self, request):
        try:
            # MAJOR CHANGE: Only clear active cart
            cart = Cart.objects.filter(
                user=request.user,
                is_ordered=False,
                is_paid=False
            ).first()
            
            if not cart:
                return Response(
                    {'message': 'No active cart found to clear'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            items_count = cart.items.count()
            cart.items.all().delete()
            
            return Response(
                {'message': f'Cart cleared successfully. Removed {items_count} items.'}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'An unexpected error occurred while clearing cart'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# NEW VIEW: Order History
class OrderHistoryView(APIView):
    """View completed orders (carts that are ordered and paid)"""
    permission_classes = [IsCustomer]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        try:
            completed_carts = Cart.objects.filter(
                user=request.user,
                is_ordered=True,
                is_paid=True
            ).order_by('-updated_at')
            
            serializer = CartSerializer(completed_carts, many=True)
            
            return Response({
                'orders': serializer.data,
                'total_orders': completed_carts.count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch order history'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )