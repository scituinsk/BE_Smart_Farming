import json, io, qrcode
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from smartfarming.utils.mqtt import publish_message
from smartfarming.utils.exc_handler import CustomResponse
from django.db.models import Sum, Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from smartfarming.utils.permissions import *
from smartfarming.tasks import task_broadcast_module_notification
from profil.models import NotificationType, Notification
from django.utils import timezone
from .models import *
from .serializers import *
from schedule.models import GroupSchedule
from schedule.serializers import GroupScheduleSerializer

class DeviceListAdminView(APIView):
    """
    Endpoint untuk mengelola daftar Device (Modul).

    - GET:
        Hanya dapat diakses oleh admin (is_staff).
        Mengembalikan daftar semua modul yang ada di sistem, diurutkan berdasarkan nama.

    - POST:
        Hanya dapat diakses oleh admin (is_staff).
        Membuat modul baru berdasarkan data request body.
    """
    permission_classes = [AdminOnlyPost, AdminOnlyGet, IsAuthenticated]

    def get(self, request):
        queryset = Modul.objects.all().order_by('name')
        serializer = ModulSerializers(queryset, many=True)
        return CustomResponse(success=True, status=status.HTTP_200_OK, message="Success", data=serializer.data, request=request)

    def post(self, request):
        serializer = ModulSerializers(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(success=True, message="Success", data=serializer.data, status=status.HTTP_201_CREATED, request=request)
        return CustomResponse(success=False, message=serializer.errors, status=status.HTTP_400_BAD_REQUEST, request=request)


class DeviceDetailAdminView(APIView):
    """
    Endpoint untuk menghapus modul berdasarkan primary key (pk).
    """
    permission_classes = [IsAuthenticated, AdminOnlyDelete, AdminOnlyPatch]

    def patch(self, request, pk):
        modul = get_object_or_404(Modul, pk=pk)
        serializer = ModulSerializers(modul, data= request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(success=True, message="Device diperbarui", data=serializer.data, status=status.HTTP_200_OK, request=request)
        return CustomResponse(success=True, message="User sudah terhubung dengan modul ini", data=None, status=status.HTTP_200_OK, request=request)

    def delete(self, request, pk):
        modul = get_object_or_404(Modul, pk=pk)
        modul.delete()
        return CustomResponse(success=True, message=f"Modul dengan id {pk} berhasil dihapus", status=status.HTTP_200_OK, request=request)


class ModulUserView(APIView):
    """
    Endpoint untuk mengelola relasi user dengan Modul tertentu.
    Menggunakan field `serial_id` untuk identifikasi modul.

    - POST:
        Cek apakah user sudah memiliki akses ke modul.
        Jika belum, user harus memasukkan password yang valid untuk mendapatkan akses.

    - GET:
        Mengambil data jika user sudah terdaftar.

    - PATCH:
        Tambahkan user ke modul (klaim modul).
        Jika user belum terhubung, wajib kirim password.

    - DELETE:
        Hapus user dari modul (unassign) tanpa menghapus modul.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, serial_id):
        modul = get_object_or_404(Modul,serial_id=serial_id)
        if modul.user.filter(id=request.user.id).exists():
            serializer = ModulSerializers(modul)
            return CustomResponse(success=True, message="Success", data=serializer.data, status=status.HTTP_200_OK, request=request)

        password = request.data.get("password")
        if not password:
            return CustomResponse(success=False, message="password diperlukan untuk mengakses modul ini", status=status.HTTP_403_FORBIDDEN, request=request)

        if password != modul.password:
            return CustomResponse(success=False, message="password salah", status=status.HTTP_403_FORBIDDEN, request=request)

        modul.user.add(request.user)

        # Push notifications and logs 
        log_data = {
            "username": request.user.username,
            "email": request.user.email,
            "modul": str(modul.serial_id),
            "timestamp": timezone.now().isoformat().replace("+00:00", "Z"),
        }
        title = "User baru melakukan klaim modul IoT"
        body = f"{request.user.username} telah ditambahkan."
        user_ids = list(modul.user.values_list('id', flat=True))
        task_broadcast_module_notification.delay(user_ids=user_ids , modul_id=modul.id, title=title, body=body, data=log_data)
        users = modul.user.all()
        Notification.bulk_create_for_users(users=users, notif_type=NotificationType.MODULE, title=title, body=body, data=log_data)

        serializer = ModulSerializers(modul)
        return CustomResponse(success=True, message="Akses diberikan dan modul berhasil ditambahkan ke akun Anda", data=serializer.data, status=status.HTTP_200_OK, request=request)

    def get(self, request, serial_id):
        modul = get_object_or_404(Modul, serial_id=serial_id)
        if modul.user.filter(id=request.user.id).exists():
            serializer = ModulSerializers(modul)
            return CustomResponse(success=True, message="Success", data=serializer.data, status=status.HTTP_200_OK, request=request)
        return CustomResponse(message="Silahkan klaim modul terlebih dahulu.", status=status.HTTP_401_UNAUTHORIZED, request=request, data="unauthorized")

    def patch(self, request, serial_id):
        modul = get_object_or_404(Modul, serial_id=serial_id)
        title = "User baru melakukan klaim modul IoT"
        body = f"{request.user.username} telah ditambahkan."
        log_data = {
            "username": request.user.username,
            "email": request.user.email,
            "modul": str(modul.serial_id),
            "timestamp": timezone.now().isoformat().replace("+00:00", "Z"),
        }

        if modul.user.filter(id=request.user.id).exists():
            serializer = ModulSerializers(modul, data= request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return CustomResponse(success=True, message="Device diperbarui", data=serializer.data, status=status.HTTP_200_OK, request=request)
            return CustomResponse(success=True, message="User sudah terhubung dengan modul ini", data=None, status=status.HTTP_200_OK, request=request)

        password = request.data.get("password")
        if not password:
            return CustomResponse(success=False, message="password diperlukan untuk klaim modul", status=status.HTTP_400_BAD_REQUEST, request=request)

        if password != modul.password:
            return CustomResponse(success=False, message="password salah", status=status.HTTP_403_FORBIDDEN, request=request)

        modul.user.add(request.user)
        user_ids = list(modul.user.values_list('id', flat=True))

        # Push notifications and logs 
        task_broadcast_module_notification.delay(user_ids=user_ids ,modul_id=modul.id, title=title, body=body, data=log_data)
        users = modul.user.all()
        Notification.bulk_create_for_users(users=users, notif_type=NotificationType.MODULE, title=title, body=body, data=log_data)

        return CustomResponse(success=True, message="User berhasil ditambahkan ke modul", data={"modul_id": modul.id, "user_id": request.user.id}, status=status.HTTP_200_OK, request=request)

    def delete(self, request, serial_id):
        modul = get_object_or_404(Modul, serial_id=serial_id)
        if not modul.user.filter(id=request.user.id).exists():
            return CustomResponse(success=False, message="User tidak terhubung dengan modul ini", status=status.HTTP_404_NOT_FOUND, request=request)

        modul.user.remove(request.user)
        return CustomResponse(success=True, message="User berhasil dihapus dari modul", data={"modul_id": modul.id, "user_id": request.user.id}, status=status.HTTP_200_OK, request=request)

class ModulListUserView(APIView):
    """
    Endpoint untuk mendapatkan daftar modul yang dimiliki user saat ini.

    GET:
    - Mengembalikan semua modul yang terhubung dengan user.
    - Hanya modul yang sudah diklaim user yang akan muncul di sini.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Modul.objects.filter(user=request.user).order_by("name")
        serializer = ModulSerializers(queryset, many=True)
        return CustomResponse(success=True, message="Success", data=serializer.data, status=status.HTTP_200_OK, request=request)

class FeatureListView(APIView):
    """
    Endpoint untuk mengelola daftar Feature.

    - GET:
        Mengambil semua fitur yang ada di sistem, diurutkan berdasarkan nama.

    - POST:
        Hanya admin yang boleh menambahkan feature baru.
    """
    permission_classes = [IsAuthenticated, AdminOnlyDelete, AdminOnlyPost]

    def get(self, request):
        queryset = Feature.objects.all().order_by("name")
        serializers = FeatureSerializers(queryset, many=True)
        return CustomResponse(success=True, message="Success", data=serializers.data, status=status.HTTP_200_OK, request=request)

    def post(self, request):
        serializer = FeatureSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(success=True, message="Success", data=serializer.data, status=status.HTTP_201_CREATED, request=request)
        return CustomResponse(success=False, message=serializer.errors, status=status.HTTP_400_BAD_REQUEST, request=request)


class ModulePinView(APIView):
    """
    Endpoint detail untuk mengelola Pin tertentu berdasarkan Modul IoT.

    - GET:
        Mengambil detail pin berdasarkan ID dan pemilik modul

    - PATCH:
        Update sebagian data pin (partial update).

    - DELETE:
        Hapus pin berdasarkan ID.
        Hanya admin yang boleh menghapus.
    """
    permission_classes = [IsAuthenticated, AdminOnlyDelete, AdminOnlyPost]

    def post(self, request, serial_id):
        module = get_object_or_404(Modul, serial_id=serial_id)
        serializer = ModulePinSerializers(data=request.data, context={'request': request, 'module': module})
        if serializer.is_valid():
            serializer.save(module=module)
            return CustomResponse(success=True, message="Success", data=serializer.data, status=status.HTTP_201_CREATED, request=request)
        return CustomResponse(success=False, message=serializer.errors, status=status.HTTP_400_BAD_REQUEST, request=request)

    def get(self, request, serial_id, pin=None):
        if pin:
            pin = get_object_or_404(ModulePin,module__serial_id=serial_id, pin=pin)
            if not pin.module.user.filter(id=request.user.id).exists():
                return CustomResponse(success=False, message="Anda bukan pemilik pin modul ini", status=status.HTTP_403_FORBIDDEN, request=request)
            serializer = ModulePinSerializers(pin)
        else:
            pins = ModulePin.objects.filter(module__serial_id = serial_id, module__user = request.user)
            serializer = ModulePinSerializers(pins, many=True)
        return CustomResponse(success=True, message="Success", data=serializer.data, status=status.HTTP_200_OK, request=request)

    def patch(self, request,serial_id, pin):
        pin = get_object_or_404(ModulePin,module__serial_id=serial_id, pin=pin)
        if not pin.module.user.filter(id=request.user.id).exists():
            return CustomResponse(success=False, message="Anda bukan pemilik pin modul ini", status=status.HTTP_403_FORBIDDEN, request=request)
        serializer = ModulePinSerializers(pin, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(success=True, message=f"PIN {pin.pin} Modul {serial_id} berhasil diperbarui", data=serializer.data, status=status.HTTP_200_OK, request=request)
        return CustomResponse(success=False, message=serializer.errors, status=status.HTTP_400_BAD_REQUEST, request=request)

    def delete(self, request, serial_id, pin):
        pin = get_object_or_404(ModulePin,module__serial_id=serial_id, pin=pin)
        pin.delete()
        return CustomResponse(success=True, message=f"PIN {pin.pin} Modul {serial_id} berhasil dihapus", data=None, status=status.HTTP_204_NO_CONTENT, request=request)
    
class ListModuleGroupView(APIView):
    """
    View untuk mengambil list group di modul (GET)
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, serial_id, user):
        """
        Helper method untuk mengambil objek group.
        Memastikan objek ada dan dimiliki oleh pengguna yang benar.
        """
        try:
            return GroupSchedule.objects.filter(modul__serial_id=serial_id, modul__user=user)
        except GroupSchedule.DoesNotExist:
            raise Http404

    def get(self, request, serial_id):
        """Mengambil list group."""
        group = self.get_object(serial_id, request.user)
        serializer = GroupScheduleSerializer(group, many=True)
        return CustomResponse(data = serializer.data, request=request)

class FeatureDetailView(APIView):
    """
    Endpoint detail untuk mengelola Feature tertentu berdasarkan ID.

    - GET:
        Mengambil detail feature berdasarkan ID

    - PATCH:
        Update sebagian data feature (partial update).
        Hanya admin yang boleh melakukan operasi ini.

    - DELETE:
        Hapus feature berdasarkan ID.
        Hanya admin yang boleh menghapus.
    """
    permission_classes = [IsAuthenticated, AdminOnlyDelete, AdminOnlyPost, AdminOnlyPatch]

    def get(self, request, id):
        serializer = FeatureSerializers(data=get_object_or_404(Feature, id=id))
        return CustomResponse(success=True, message="Success", data=serializer.data, status=status.HTTP_200_OK, request=request)

    def patch(self, request, id):
        feature = get_object_or_404(Feature, id=id)
        serializer = FeatureSerializers(feature, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(success=True, message=f"Feature dengan id {id} berhasil diperbarui", data=serializer.data, status=status.HTTP_200_OK, request=request)
        return CustomResponse(success=False, message=serializer.errors, status=status.HTTP_400_BAD_REQUEST, request=request)

    def delete(self, request, id):
        feature = get_object_or_404(Feature, id=id)
        feature.delete()
        return CustomResponse(success=True, message=f"Feature dengan id {id} berhasil dihapus", data=None, status=status.HTTP_204_NO_CONTENT, request=request)

class ModulQRCodeView(APIView):
    """
    Endpoint untuk men-generate dan menampilkan gambar QR code
    berdasarkan serial_id sebuah Modul.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, serial_id):
        modul = get_object_or_404(Modul, serial_id=serial_id)
        # Ambil serial_id sebagai data untuk di-encode
        qr_data = str(modul.serial_id)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Simpan gambar ke buffer di memori (bukan file fisik)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        # Pindahkan "cursor" buffer ke awal file
        buffer.seek(0)
        return HttpResponse(buffer, content_type='image/png')
    
class ControlDeviceView(APIView):
    """
    Endpoint untuk mengirim perintah ke perangkat melalui MQTT.
    """
    def post(self, request, *args, **kwargs):
        device_id = request.data.get('device_id')
        command = request.data.get('command')
        print(request.data)

        if not device_id or not command:
            return Response(
                {"error": "device_id and command are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        topic = f"devices/{device_id}/control"
        payload = json.dumps({"command": command, "source": "api"})

        # Kirim pesan
        success = publish_message(topic, payload)
        # success = True

        if success:
            return Response(
                {"message": f"Command '{command}' sent to device '{device_id}'."},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "Failed to send command via MQTT."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class LogsListAllAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        """Mengambil detail log modul."""
        logs = (
        ModuleLog.objects.filter(module__user = request.user)
            .select_related("module", "schedule")
            .order_by("-created_at")
            .distinct()
            )
        serializer = ModuleLogSerializer(logs, many=True)
        return CustomResponse(data = serializer.data, status=status.HTTP_200_OK, request=request)

class LogsListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, serial_id):
        """Mengambil detail log modul."""
        modul = get_object_or_404(Modul, serial_id=serial_id)
        is_member = modul.user.filter(pk=request.user.pk).exists()

        if not is_member:
            return CustomResponse(message="Anda tidak memiliki izin untuk melihat log modul ini.", status=status.HTTP_403_FORBIDDEN, request=request)
        logs = ModuleLog.objects.filter(module = modul).order_by("-updated_at")
        serializer = ModuleLogSerializer(logs, many=True)
        return CustomResponse(data = serializer.data, status=status.HTTP_200_OK, request=request)
    
class LogsDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        """
        Menghapus satu entitas log berdasarkan ID-nya.
        """
        log_object = get_object_or_404(ModuleLog, id=id)
        is_member = log_object.module.user.filter(pk=request.user.pk).exists()

        if not is_member:
            return CustomResponse(message="Anda tidak memiliki izin untuk menghapus log ini.", status=status.HTTP_403_FORBIDDEN, request=request)
        log_object.delete()
        return CustomResponse(message="Log berhasil dihapus.", status=status.HTTP_200_OK, request=request)