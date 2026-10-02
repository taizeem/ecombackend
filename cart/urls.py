from django.urls import path
from .views import CartViewSet

urlpatterns = [
    path("", CartViewSet.as_view({"get": "list"}), name="cart-detail"),
    path("items/", CartViewSet.as_view({"post": "add_item"}), name="cart-add-item"),
    path("items/<uuid:pk>/", CartViewSet.as_view({"patch": "update_item", "delete": "remove_item"}), name="cart-item-detail"),
    path("clear/", CartViewSet.as_view({"delete": "clear_cart"}), name="cart-clear"),
]