from rest_framework import serializers
from .models import Category, Product, ProductImage


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
    seller_username = serializers.CharField(source="seller.username", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "seller",
            "seller_username",
            "category",
            "description",
            "price",
            "compare_at_price",
            "stock",
            "is_in_stock",
            "is_active",
            "average_rating",
            "review_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


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





class SellerProductSerializer(serializers.ModelSerializer):
    seller_username = serializers.CharField(source="seller.username", read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "seller",
            "seller_username",
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
        # 'seller' is set automatically from the request user, never passed manually
        read_only_fields = ["id", "slug", "seller", "created_at", "updated_at"]

    def validate(self, attrs):
        price = attrs.get("price")
        compare_at_price = attrs.get("compare_at_price")

        if compare_at_price and price and compare_at_price <= price:
            raise serializers.ValidationError(
                {"compare_at_price": "Compare-at price (MSRP) must be greater than current price."}
            )
        return attrs


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "is_feature", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProductImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "is_feature"]

    def validate_image(self, file):
        # Enforce max file size: 5MB
        max_size_mb = 5
        if file.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError(f"Image size cannot exceed {max_size_mb}MB.")
        return file


# Update ProductReadSerializer to nest images:
class ProductReadSerializer(serializers.ModelSerializer):
    category = SimpleCategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "seller",
            "category",
            "description",
            "price",
            "compare_at_price",
            "stock",
            "is_in_stock",
            "is_active",
            "images",  # <-- Nested array of image objects
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


# Update SellerProductSerializer to also show existing images:
class SellerProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

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
            "is_active",
            "images",  # <-- Shows uploaded images to the seller
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]