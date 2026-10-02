import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from products.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Payment"
        PROCESSING = "PROCESSING", "Processing"
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Shipping details
    shipping_address = models.TextField()
    phone_number = models.CharField(max_length=20)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order #{str(self.id)[:8]} - {self.user.username} ({self.status})"


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sold_items",
    )
    product_name = models.CharField(max_length=255)  # Snapshot name
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Snapshot price at purchase
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product_name} ($ {self.price})"