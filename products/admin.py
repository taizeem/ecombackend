from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "product_count", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_active",)
    ordering = ("name",)

    def get_queryset(self, request):
        """Annotate queryset with product count to avoid extra queries in list view."""
        qs = super().get_queryset(request)
        return qs.prefetch_related("products")

    @admin.display(description="Products")
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "compare_at_price",
        "stock",
        "inventory_status",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "category", "created_at")
    search_fields = ("name", "slug", "description", "id")
    prepopulated_fields = {"slug": ("name",)}
    
    # Quick inline updates without opening the detail page
    list_editable = ("price", "stock", "is_active")
    
    # Replaces slow dropdown select with a searchable AJAX modal for large catalogs
    autocomplete_fields = ("category",)
    
    # Avoids N+1 queries on the foreign key relationship
    list_select_related = ("category",)
    
    # Read-only fields that shouldn't be edited by hand
    readonly_fields = ("id", "created_at", "updated_at")
    
    # Organized fieldsets for the edit view
    fieldsets = (
        ("Identification", {
            "fields": ("id", "name", "slug", "category", "description")
        }),
        ("Pricing & Inventory", {
            "fields": ("price", "compare_at_price", "stock")
        }),
        ("Visibility & Status", {
            "fields": ("is_active",)
        }),
        ("Audit Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),  # Collapsed by default
        }),
    )

    @admin.display(description="Stock Status")
    def inventory_status(self, obj):
        if obj.stock <= 0:
            return format_html('<span style="color: red; font-weight: bold;">Out of Stock</span>')
        if obj.stock < 10:
            return format_html('<span style="color: orange; font-weight: bold;">Low Stock ({})</span>', obj.stock)
        return format_html('<span style="color: green;">In Stock</span>')