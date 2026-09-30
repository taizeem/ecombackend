import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        BUYER = "BUYER", "Buyer"
        SELLER = "SELLER", "Seller"
        ADMIN = "ADMIN", "Admin"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.BUYER,
        db_index=True,
    )

    # Optional business metadata
    phone_number = models.CharField(max_length=20, blank=True, default="")

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    @property
    def is_seller(self) -> bool:
        return self.role == self.Role.SELLER or self.is_staff

    @property
    def is_buyer(self) -> bool:
        return self.role == self.Role.BUYER

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"