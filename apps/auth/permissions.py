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
