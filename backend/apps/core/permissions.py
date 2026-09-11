from rest_framework.permissions import SAFE_METHODS, BasePermission


class ReadOnlyOrAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or bool(request.user and request.user.is_authenticated)


class AdminWritePermission(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or bool(request.user and request.user.is_staff)
