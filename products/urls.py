from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, SellerProductViewSet,SellerProductImageViewSet

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"products", ProductViewSet, basename="public-product")
router.register(r"seller/products", SellerProductViewSet, basename="seller-product")

urlpatterns = [
    path("", include(router.urls)),
    # Nested image management routes:
    path(
        "seller/products/<uuid:product_id>/images/",
        SellerProductImageViewSet.as_view({"get": "list", "post": "create"}),
        name="seller-product-images-list",
    ),
    path(
        "seller/products/<uuid:product_id>/images/<uuid:pk>/",
        SellerProductImageViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="seller-product-images-detail",
    ),
]