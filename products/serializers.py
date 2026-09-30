from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "product_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["slug", "created_at", "updated_at"]


# Minimal embedded representation of a Category inside a Product response
class SimpleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ProductReadSerializer(serializers.ModelSerializer):
    category = SimpleCategorySerializer(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "description",
            "price",
            "compare_at_price",
            "stock",
            "is_in_stock",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "description",
            "price",
            "compare_at_price",
            "stock",
            "is_active",
        ]

    def validate(self, attrs):
        price = attrs.get("price")
        compare_at_price = attrs.get("compare_at_price")

        if compare_at_price and price and compare_at_price <= price:
            raise serializers.ValidationError(
                {"compare_at_price": "Compare-at price (MSRP) must be greater than current price."}
            )
        return attrs