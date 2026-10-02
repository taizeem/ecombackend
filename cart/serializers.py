from rest_framework import serializers
from products.serializers import ProductReadSerializer
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductReadSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "subtotal", "created_at"]
        read_only_fields = ["id", "subtotal", "created_at"]

    def validate_product_id(self, value):
        from products.models import Product
        try:
            product = Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product does not exist or is inactive.")
        return value

    def validate(self, attrs):
        # Check stock availability when adding or updating quantity
        product_id = attrs.get("product_id") or (self.instance.product.id if self.instance else None)
        quantity = attrs.get("quantity", 1)

        if product_id:
            from products.models import Product
            product = Product.objects.get(id=product_id)
            if product.stock < quantity:
                raise serializers.ValidationError(
                    {"quantity": f"Requested quantity exceeds available stock ({product.stock} available)."}
                )
        return attrs


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "user", "items", "total_price", "updated_at"]
        read_only_fields = ["id", "user", "total_price", "updated_at"]