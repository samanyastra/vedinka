from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from typing import Any

    
class IsAdmin(BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.profile.role.name == "admin"
        )


class IsAuthor(BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.profile.role.name == "author"
        )


class IsUser(BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.profile.role.name == "user"
        )


class IsSuperUserOrAdmin(BasePermission):
    """Permission class to check if user is superuser or admin.
    
    Returns True if user is Django superuser or has 'admin' role.
    Used for admin-only endpoints like subscription management.
    """
    def has_permission(self, request: Request, view: Any) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_superuser
                or (
                    request.user.profile
                    and request.user.profile.role
                    and request.user.profile.role.name == "admin"
                )
            )
        )
