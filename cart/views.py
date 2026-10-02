from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer


class CartViewSet(viewsets.ViewSet):
    """
    Manage the authenticated user's shopping cart.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_cart(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def list(self, request):
        cart = self.get_cart()
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="items")
    def add_item(self, request):
        cart = self.get_cart()
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data["product_id"]
        quantity = serializer.validated_data["quantity"]

        # If item already exists in cart, update quantity instead of throwing unique constraint error
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_id=product_id,
            defaults={"quantity": quantity},
        )

        if not created:
            cart_item.quantity += quantity
            # Re-validate stock against updated total quantity
            if cart_item.product.stock < cart_item.quantity:
                return Response(
                    {"error": f"Total quantity exceeds stock limit ({cart_item.product.stock})."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cart_item.save()

        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="items")
    def update_item(self, request, pk=None):
        cart = self.get_cart()
        try:
            cart_item = CartItem.objects.get(id=pk, cart=cart)
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CartItemSerializer(cart_item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["delete"], url_path="items")
    def remove_item(self, request, pk=None):
        cart = self.get_cart()
        try:
            cart_item = CartItem.objects.get(id=pk, cart=cart)
            cart_item.delete()
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["delete"], url_path="clear")
    def clear_cart(self, request):
        cart = self.get_cart()
        cart.items.all().delete()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)