# products/views.py - Add this new view for public product listing
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import Http404
import logging
from .models import Category, Products
from .serializers import CategorySerializer, ProductSerializer

logger = logging.getLogger(__name__)

class IsVendor(permissions.BasePermission):
    """
    Custom permission to only allow vendors to create/edit/delete products
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'role') and request.user.role == 'vendor'

    def has_object_permission(self, request, view, obj):
        # Object-level permission to only allow owners of an object to edit it
        if not request.user or not request.user.is_authenticated:
            return False
        return obj.vendor == request.user

# NEW: Public product list view for customers
class PublicProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]  # Allow anyone to view products
    queryset = Products.objects.all()

class ProductCreateView(generics.CreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsVendor]
    parser_classes = [MultiPartParser, FormParser]
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        logger.info(f"Creating product for user: {self.request.user}")
        serializer.save(vendor=self.request.user)

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get_queryset(self):
        # Return only products belonging to the authenticated user (for vendors)
        logger.info(f"Fetching products for user: {self.request.user}")
        return Products.objects.filter(vendor=self.request.user)

# NEW: Public product detail view
class PublicProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Products.objects.all()

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsVendor]
    authentication_classes = [JWTAuthentication]
    
    def get_queryset(self):
        # Filter products by the current vendor
        return Products.objects.filter(vendor=self.request.user)
    
    def get_object(self):
        """
        Override get_object to provide better error handling and logging
        """
        queryset = self.get_queryset()
        pk = self.kwargs.get('pk')
        
        logger.info(f"Attempting to get product {pk} for user {self.request.user}")
        
        try:
            obj = queryset.get(pk=pk)
            # Check permissions
            self.check_object_permissions(self.request, obj)
            return obj
        except Products.DoesNotExist:
            logger.warning(f"Product {pk} not found for user {self.request.user}")
            raise Http404("Product not found or you don't have permission to access it")
    
    def retrieve(self, request, *args, **kwargs):
        """Handle GET requests"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Http404 as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def update(self, request, *args, **kwargs):
        """Handle PUT/PATCH requests"""
        try:
            return super().update(request, *args, **kwargs)
        except Http404 as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def destroy(self, request, *args, **kwargs):
        """Handle DELETE requests"""
        try:
            instance = self.get_object()
            logger.info(f"Deleting product {instance.id} ({instance.title}) for user {request.user}")
            
            # Store product info for response
            product_title = instance.title
            
            # Perform the deletion
            instance.delete()
            
            logger.info(f"Successfully deleted product: {product_title}")
            
            return Response(
                {
                    "message": f"Product '{product_title}' deleted successfully"
                }, 
                status=status.HTTP_200_OK
            )
        except Http404 as e:
            logger.error(f"Failed to delete product: {str(e)}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Unexpected error during product deletion: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred while deleting the product"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    permission_classes = [IsVendor]
    authentication_classes = [JWTAuthentication]

    def list(self, request, *args, **kwargs):
        """Handle GET requests for listing categories"""
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            return Response(
                {"error": "Failed to fetch categories"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """Handle POST requests for creating categories"""
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error creating category: {str(e)}")
            return Response(
                {"error": "Failed to create category"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    permission_classes = [IsVendor]
    authentication_classes = [JWTAuthentication]