import json, io, qrcode
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from smartfarming.utils.mqtt import publish_message
from smartfarming.utils.exc_handler import CustomResponse
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from smartfarming.utils.permissions import *
from .models import *
from .serializers import *

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
    permission_classes = [AdminOnlyPost, IsAuthenticated]

    def get(self, request):
        queryset = Modul.objects.all().order_by('name')
        serializer = ModulSerializers(queryset, many=True)
        return CustomResponse(success=True, status=status.HTTP_200_OK, message="Success", data=serializer.data)

    def post(self, request):
        serializer = ModulSerializers(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(success=True, message="Success", data=serializer.data, status=status.HTTP_201_CREATED)
        return CustomResponse(success=False, message="Validation failed", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeviceDetailAdminView(APIView):
    """
    Endpoint untuk menghapus modul berdasarkan primary key (pk).
    """
    permission_classes = [IsAuthenticated, AdminOnlyDelete]

    def patch(self, request, pk):
        modul = get_object_or_404(Modul, pk=pk)
        serializer = ModulSerializers(modul, data= request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(success=True, message="Device diperbarui", data=serializer.data, status=status.HTTP_200_OK)
        return CustomResponse(success=True, message="User sudah terhubung dengan modul ini", data=None, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        modul = get_object_or_404(Modul, pk=pk)
        modul.delete()
        return CustomResponse(success=True, message=f"Modul dengan id {pk} berhasil dihapus", status=status.HTTP_200_OK)


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
            return CustomResponse(success=True, message="Success", data=serializer.data, status=status.HTTP_200_OK)

        password = request.data.get("password")
        if not password:
            return CustomResponse(success=False, message="password diperlukan untuk mengakses modul ini", errors={"password": ["Field required"]}, status=status.HTTP_403_FORBIDDEN)

        if password != modul.password:
            return CustomResponse(success=False, message="password salah", errors={"password": ["Invalid password"]}, status=status.HTTP_403_FORBIDDEN)

        modul.user.add(request.user)
        serializer = ModulSerializers(modul)
        return CustomResponse(success=True, message="Akses diberikan dan modul berhasil ditambahkan ke akun Anda", data=serializer.data, status=status.HTTP_200_OK)

    def get(self, request, serial_id):
        modul = get_object_or_404(Modul, serial_id=serial_id)
        if modul.user.filter(id=request.user.id).exists():
            serializer = ModulSerializers(modul)
            return CustomResponse(success=True, message="Success", data=serializer.data, status=status.HTTP_200_OK)
        return CustomResponse(message="Silahkan klaim modul terlebih dahulu.", status=status.HTTP_401_UNAUTHORIZED)

    def patch(self, request, serial_id):
        modul = get_object_or_404(Modul, serial_id=serial_id)

        if modul.user.filter(id=request.user.id).exists():
            serializer = ModulSerializers(modul, data= request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return CustomResponse(success=True, message="Device diperbarui", data=serializer.data, status=status.HTTP_200_OK)
            return CustomResponse(success=True, message="User sudah terhubung dengan modul ini", data=None, status=status.HTTP_200_OK)

        password = request.data.get("password")
        if not password:
            return CustomResponse(success=False, message="password diperlukan untuk klaim modul", errors={"password": ["Field required"]}, status=status.HTTP_400_BAD_REQUEST)

        if password != modul.password:
            return CustomResponse(success=False, message="password salah", errors={"password": ["Invalid password"]}, status=status.HTTP_403_FORBIDDEN)

        modul.user.add(request.user)
        return CustomResponse(success=True, message="User berhasil ditambahkan ke modul", data={"modul_id": modul.id, "user_id": request.user.id}, status=status.HTTP_200_OK)

    def delete(self, request, serial_id):
        modul = get_object_or_404(Modul, serial_id=serial_id)
        if not modul.user.filter(id=request.user.id).exists():
            return CustomResponse(success=False, message="User tidak terhubung dengan modul ini", errors={"user": ["Not assigned"]}, status=status.HTTP_404_NOT_FOUND)

        modul.user.remove(request.user)
        return CustomResponse(success=True, message="User berhasil dihapus dari modul", data={"modul_id": modul.id, "user_id": request.user.id}, status=status.HTTP_200_OK)

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
        return CustomResponse(success=True, message="Success", data=serializer.data, status=status.HTTP_200_OK, )

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
        return CustomResponse(success=True, message="Success", data=serializers.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = FeatureSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(success=True, message="Success", data=serializer.data, status=status.HTTP_201_CREATED)
        return CustomResponse(success=False, message="Validation failed", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        return CustomResponse(success=True, message="Success", data=serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id):
        feature = get_object_or_404(Feature, id=id)
        serializer = FeatureSerializers(feature, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(success=True, message=f"Feature dengan id {id} berhasil diperbarui", data=serializer.data, status=status.HTTP_200_OK)
        return CustomResponse(success=False, message="Validation failed", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        feature = get_object_or_404(Feature, id=id)
        feature.delete()
        return CustomResponse(success=True, message=f"Feature dengan id {id} berhasil dihapus", data=None, status=status.HTTP_204_NO_CONTENT)

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