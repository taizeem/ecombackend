from rest_framework import permissions


class IsSellerOrReadOnly(permissions.BasePermission):
    """
    - Read permissions are allowed to any request (Buyer or anonymous).
    - Write permissions (create) are only allowed to authenticated Sellers or Staff.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == "SELLER" or request.user.is_staff)
        )


class IsProductSellerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission:
    Only the seller who created the product can edit/delete it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Staff can moderate any product; otherwise must be the owner
        return obj.seller == request.user or request.user.is_staff


class IsSellerUser(permissions.BasePermission):
    """
    Allows access only to authenticated users with the SELLER role (or staff).
    """
    message = "Only registered sellers have access to manage inventory."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (getattr(request.user, "role", None) == "SELLER" or request.user.is_staff)
        )