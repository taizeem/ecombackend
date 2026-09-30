import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.conf import settings


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides self-updating
    'created_at' and 'updated_at' fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True, db_index=True)
    slug = models.SlugField(max_length=160, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    # UUID primary key prevents sequential ID enumeration attacks in public APIs
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete= models.CASCADE,
        related_name="products",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,  # Prevents accidental cascade deletion of products when a category is deleted
        related_name="products",
    )

    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=270, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")

    # DecimalField is mandatory for financial precision (never use FloatField)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    compare_at_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original price for showing discounts (MSRP)",
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Use this to hide products without deleting historical sales records",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["seller", "is_active"]),
            # Composite index for filtering active products inside a category
            models.Index(fields=["category", "is_active"]),
            # Composite index for sorting active products by price
            models.Index(fields=["is_active", "price"]),
        ]
        constraints = [
            # Database-level guarantee that stock never drops below 0
            models.CheckConstraint(
                condition=models.Q(stock__gte=0),
                name="stock_non_negative",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            # Append short UUID suffix if needed, or slugify name
            base_slug = slugify(self.name)
            self.slug = f"{base_slug}-{str(self.id)[:8]}" if Product.objects.filter(slug=base_slug).exists() else base_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (${self.price})"

    @property
    def is_in_stock(self) -> bool:
        return self.stock > 0