from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "seller", "product_name", "price", "quantity", "subtotal"]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "user_username",
            "status",
            "total_amount",
            "shipping_address",
            "phone_number",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "status", "total_amount", "created_at", "updated_at"]


class CheckoutSerializer(serializers.Serializer):
    shipping_address = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True, max_length=20)