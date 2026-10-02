from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_staff", "date_joined")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email")
    fieldsets = UserAdmin.fieldsets + (
        ("Role & Metadata", {"fields": ("role", "phone_number")}),
    )