from rest_framework.permissions import BasePermission

class IsSwaggerAllowed(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff

class AdminOnlyPost(BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return request.user and request.user.is_staff
        return True

class AdminOnlyDelete(BasePermission):
    def has_permission(self, request, view):
        if request.method == "DELETE":
            return request.user and request.user.is_staff
        return True

class AdminOnlyPatch(BasePermission):
    def has_permission(self, request, view):
        if request.method == "PATCH":
            return request.user and request.user.is_staff
        return True

class AdminOnlyPut(BasePermission):
    def has_permission(self, request, view):
        if request.method == "PUT":
            return request.user and request.user.is_staff
        return True

class AdminOnlyGet(BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET":
            return request.user and request.user.is_staff
        return True