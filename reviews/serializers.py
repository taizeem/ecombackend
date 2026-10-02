from rest_framework import serializers
from orders.models import Order
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "product",
            "user",
            "user_username",
            "rating",
            "comment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        product = attrs.get("product") or (self.instance.product if self.instance else None)
        user = request.user

        # Verified Purchase Validation on creation
        if not self.instance and product:
            has_purchased = Order.objects.filter(
                user=user,
                items__product=product,
                status__in=[
                    Order.Status.PROCESSING,
                    Order.Status.SHIPPED,
                    Order.Status.DELIVERED,
                ],
            ).exists()

            if not has_purchased:
                raise serializers.ValidationError(
                    {"product": "You can only review products that you have successfully purchased."}
                )

        return attrs