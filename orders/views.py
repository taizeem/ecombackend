from decimal import Decimal
from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from cart.models import Cart
from products.models import Product
from .models import Order, OrderItem
from .serializers import OrderSerializer, CheckoutSerializer, OrderStatusUpdateSerializer


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.prefetch_related("items", "items__product", "items__seller")
        # Admins see all orders, Sellers see orders containing their items, Buyers see their own orders
        if user.is_staff:
            return qs.all()
        elif getattr(user, "role", None) == "SELLER":
            # Orders containing items sold by this seller
            return qs.filter(items__seller=user).distinct()
        return qs.filter(user=user)

    @action(detail=False, methods=["post"], url_path="checkout")
    def checkout(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        shipping_address = serializer.validated_data["shipping_address"]
        phone_number = serializer.validated_data["phone_number"]

        try:
            cart = Cart.objects.prefetch_related("items__product", "items__product__seller").get(user=request.user)
        except Cart.DoesNotExist:
            return Response({"error": "No active cart found."}, status=status.HTTP_400_BAD_REQUEST)

        cart_items = cart.items.all()
        if not cart_items.exists():
            return Response({"error": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        # ATOMIC TRANSACTION & CONCURRENCY LOCKING
        try:
            with transaction.atomic():
                # 1. Collect all product IDs and lock database rows to prevent race conditions
                product_ids = [item.product.id for item in cart_items if item.product]
                locked_products = {
                    p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)
                }

                total_amount = Decimal("0.00")
                order_items_to_create = []

                # 2. Validate stock and calculate totals
                for cart_item in cart_items:
                    product = locked_products.get(cart_item.product.id)

                    if not product or not product.is_active:
                        raise ValueError(f"Product '{cart_item.product.name}' is no longer available.")

                    if product.stock < cart_item.quantity:
                        raise ValueError(
                            f"'{product.name}' only has {product.stock} units left in stock. Please update your cart."
                                )

                    item_subtotal = product.price * cart_item.quantity
                    total_amount += item_subtotal

                    # Prepare order item metadata
                    order_items_to_create.append(
                        OrderItem(
                            product=product,
                            seller=product.seller,
                            product_name=product.name,
                            price=product.price,
                            quantity=cart_item.quantity,
                        )
                    )

                    # Deduct stock safely
                    product.stock -= cart_item.quantity
                    product.save(update_fields=["stock"])

                # 3. Create the Order
                order = Order.objects.create(
                    user=request.user,
                    total_amount=total_amount,
                    shipping_address=shipping_address,
                    phone_number=phone_number,
                    status=Order.Status.PENDING,
                )

                # 4. Attach order to items and bulk create
                for item in order_items_to_create:
                    item.order = order
                OrderItem.objects.bulk_create(order_items_to_create)

                # 5. Clear the shopping cart
                cart.items.all().delete()

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Checkout failed due to an unexpected error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    
    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        """
        Allows Admins/Staff to update any order status,
        and Sellers to update status ONLY for orders containing their products.
        """
        order = self.get_object()
        user = request.user

        # Granular permission check
        if not user.is_staff:
            if getattr(user, "role", None) == "SELLER":
                # Verify this seller actually has items inside this order
                has_seller_item = order.items.filter(seller=user).exists()
                if not has_seller_item:
                    return Response(
                        {"error": "You do not have permission to update an order that contains no products from your inventory."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            else:
                return Response(
                    {"error": "You do not have permission to update order statuses."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)