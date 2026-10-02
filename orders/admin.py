from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "seller", "product_name", "price", "quantity"]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__username", "shipping_address")
    inlines = [OrderItemInline]
    readonly_fields = ["total_amount", "created_at", "updated_at"]