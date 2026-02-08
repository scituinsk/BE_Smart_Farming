from rest_framework.permissions import BasePermission
from iot.models import Modul
import uuid

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

class IsModulAuthenticated(BasePermission):
    """
    Custom Permission untuk memverifikasi IoT Device
    berdasarkan 'X-Serial-ID' dan 'X-Auth-ID' di header.
    """
    message = "Invalid Serial ID or Auth ID."

    def has_permission(self, request, view):
        # Client harus mengirim header: X-Serial-ID dan X-Auth-ID
        serial_id_str = request.headers.get('X-Serial-ID') or request.META.get('HTTP_X_SERIAL_ID')
        auth_id_str = request.headers.get('X-Auth-ID') or request.META.get('HTTP_X_Auth_ID')

        if not serial_id_str or not auth_id_str:
            return False

        # Validasi apakah string tersebut format UUID yang valid?
        # Langkah ini penting agar database tidak error 500 jika dikirim string sampah
        try:
            uuid.UUID(str(serial_id_str))
            uuid.UUID(str(auth_id_str))
        except ValueError:
            return False

        try:
            modul = Modul.objects.get(serial_id=serial_id_str, auth_id=auth_id_str)
            
            # [PENTING] Attach object modul ke request
            # Supaya di View nanti tidak perlu query ulang (Optimasi)
            request.modul = modul 
            return True
            
        except Modul.DoesNotExist:
            return False