from django.db.models import Count
from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from .filters import ProductFilter
from .models import Category, Product
from .pagination import StandardResultsSetPagination
from .serializers import (
    CategorySerializer,
    ProductReadSerializer,
    ProductWriteSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.annotate(product_count=Count("products")).order_by("name")
    serializer_class = CategorySerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "product_count"]

    def get_permissions(self):
        # Public read, admin-only write
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class ProductViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at", "stock", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        # select_related avoids N+1 queries when fetching category data
        queryset = Product.objects.select_related("category")

        # Non-staff users should only see active products
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True, category__is_active=True)

        return queryset

    def get_serializer_class(self):
        # Read operations return nested category; Write operations accept FK ID
        if self.action in ["create", "update", "partial_update"]:
            return ProductWriteSerializer
        return ProductReadSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]