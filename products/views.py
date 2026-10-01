from django.db.models import Count
from rest_framework import  viewsets, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from .filters import ProductFilter
from .permissions import IsSellerUser
from .models import Category, Product, ProductImage
from .pagination import StandardResultsSetPagination
from .serializers import (
    CategorySerializer,
    ProductReadSerializer,
    ProductWriteSerializer,
    SellerProductSerializer,
    ProductImageSerializer,
    ProductImageUploadSerializer
)
from .permissions import IsSellerOrReadOnly, IsProductSellerOrReadOnly, IsSellerUser


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.annotate(product_count=Count("products")).order_by("name")
    serializer_class = CategorySerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "product_count"]

    # def get_permissions(self):
    #     # Public read, admin-only write
    #     if self.action in ["list", "retrieve"]:
    #         return [permissions.AllowAny()]
    #     return [permissions.IsAdminUser()]


class ProductViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at", "stock", "name"]
    ordering = ["-created_at"]
    queryset = Product.objects.select_related("category", "seller").filter(is_active=True)
    permission_classes=[IsProductSellerOrReadOnly, IsSellerOrReadOnly]
   

    def get_serializer_class(self):
        # Read operations return nested category; Write operations accept FK ID
        if self.action in ["create", "update", "partial_update"]:
            return ProductWriteSerializer
        return ProductReadSerializer
    def perfrom_create(self, serialzer):
        serialzer.save(seller=self.request.user)




class SellerProductViewSet(viewsets.ModelViewSet):
    """
    Dedicated endpoint for sellers:
    - Lists ONLY products belonging to the logged-in seller (both active and inactive).
    - Automatically assigns request.user as the seller upon creation.
    - Prevents modifying or viewing other sellers' products.
    """
    serializer_class = SellerProductSerializer
    permission_classes = [IsSellerUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "stock", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        # Strict multi-tenant isolation: sellers only ever see their own records
        return (
            Product.objects.filter(seller=self.request.user)
            .select_related("category", "seller")
        )

    def perform_create(self, serializer):
        # Automatically inject logged-in seller
        serializer.save(seller=self.request.user)




from .models import Product, ProductImage
from .permissions import IsSellerUser
from .serializers import ProductImageSerializer, ProductImageUploadSerializer


class SellerProductImageViewSet(viewsets.ModelViewSet):
    """
    Handles image operations for a specific product.
    Only the product's seller can upload, view, or delete images.
    """
    permission_classes = [IsSellerUser]
    parser_classes = [MultiPartParser, FormParser]  # Required for file uploads

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProductImageUploadSerializer
        return ProductImageSerializer

    def get_product(self):
        # Guarantees the product exists AND belongs to the logged-in seller
        return get_object_or_404(
            Product,
            id=self.kwargs["product_id"],
            seller=self.request.user,
        )

    def get_queryset(self):
        return ProductImage.objects.filter(product=self.get_product())

    def perform_create(self, serializer):
        product = self.get_product()
        # If this image is marked as feature/primary, unmark other images for this product
        if serializer.validated_data.get("is_feature", False):
            ProductImage.objects.filter(product=product, is_feature=True).update(is_feature=False)
        serializer.save(product=product)