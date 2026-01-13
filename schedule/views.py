from django.http import Http404
from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from smartfarming.utils.exc_handler import CustomResponse
from smartfarming.utils.permissions import *
from iot.models import Modul
from .models import *
from .serializers import *

class AlarmListCreateAPIView(APIView):
    """
    View untuk menampilkan daftar alaram (GET) dan membuat alaram baru (POST).
    Hanya pengguna yang terautentikasi yang bisa mengakses.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        """Mengembalikan daftar alaram milik pengguna yang sedang login."""
        alarms = Alarm.objects.filter(group__modul__user=request.user)
        serializer = AlarmSerializer(alarms, many=True)
        return CustomResponse(success= True, message= "Daftar alarm User",data = serializer.data)

    def post(self, request, format=None):
        """Membuat alaram baru untuk pengguna yang sedang login."""
        try :
            group = get_object_or_404(GroupSchedule, id=request.data.get("group"))
        except:
            return CustomResponse(message="Group tidak ditemukan", status=status.HTTP_404_NOT_FOUND)

        if not group.modul.user.filter(username__iexact=request.user.username).exists():
            return CustomResponse(message="Anda tidak mempunyai modul ini", status=status.HTTP_403_FORBIDDEN)
        
        # Cek apakah modul memiliki feature bernama 'schedule'
        if not group.modul.feature.filter(name__iexact='schedule').exists():
            return CustomResponse(message="Modul ini tidak memiliki fitur 'schedule'.", data=None, status=status.HTTP_403_FORBIDDEN)
        
        serializer = AlarmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save() 
            return CustomResponse(message="Alaram berhasil ditambahkan.",data = serializer.data, status=status.HTTP_201_CREATED)
        return CustomResponse(message="Masukkan dengan format (HH:MM:SS).", data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AlarmDetailAPIView(APIView):
    """
    View untuk mengambil (GET), memperbarui (PATCH), atau menghapus (DELETE) 
    satu instance alaram.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        """
        Helper method untuk mengambil objek alaram.
        Memastikan objek ada dan dimiliki oleh pengguna yang benar.
        """
        try:
            return Alarm.objects.get(pk=pk, group__modul__user=user)
        except Alarm.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """Mengambil detail satu alaram."""
        alarm = self.get_object(pk, request.user)
        serializer = AlarmSerializer(alarm)
        return CustomResponse(data = serializer.data)

    def patch(self, request, pk, format=None):
        """Memperbarui satu alaram."""
        alarm = self.get_object(pk, request.user)
        serializer = AlarmSerializer(alarm, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(data = serializer.data)
        return CustomResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Menghapus satu alaram."""
        alarm = self.get_object(pk, request.user)
        alarm.delete()
        return CustomResponse(message="Alaram berhasil dihapus.",status=status.HTTP_204_NO_CONTENT)
    

class GroupScheduleView(APIView):
    "CRUD Grup Schedule dengan verifikasi user yang sudah terdaftar di modul dan tambahan informasi daftar pin yang terhubung"

    permission_classes = [IsAuthenticated]

    def _check_user_ownership(self, modul, user):
        """Pastikan user adalah pemilik modul dari schedule"""
        if not modul.user.filter(id=user.id).exists():
            return False
        return True

    def get(self, request, id=None):
        if id:
            group = get_object_or_404(GroupSchedule, id=id)
            if not self._check_user_ownership(group.modul, request.user):
                return CustomResponse(success=False, message="Anda bukan pemilik modul dari jadwal ini", status=status.HTTP_403_FORBIDDEN )
            serializer = GroupScheduleSerializer(group)
            return CustomResponse(success=True, message="Detail group schedule", data=serializer.data)
        else:
            # Ambil semua group milik modul user (lewat modul.user)
            groups = GroupSchedule.objects.filter(modul__user=request.user)
            serializer = GroupScheduleSerializer(groups, many=True)
            return CustomResponse(success=True, message="Daftar Group Schedule", data=serializer.data)

    def post(self, request):
        serializer = GroupScheduleSerializer(data=request.data)
        if serializer.is_valid():
            modul = serializer.validated_data.get('modul')
            if not modul:
                return CustomResponse(success=False, message="Field modul wajib diisi", status=status.HTTP_400_BAD_REQUEST)

            if not self._check_user_ownership(modul, request.user):
                return CustomResponse(success=False, message="Anda bukan pemilik modul dari schedule ini", status=status.HTTP_403_FORBIDDEN )

            serializer.save()
            return CustomResponse(success=True, message="Group Schedule berhasil dibuat", data=serializer.data, status=status.HTTP_201_CREATED)

        return CustomResponse(success=False, message="Validation failed", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        group = get_object_or_404(GroupSchedule, id=id)
        if not self._check_user_ownership(group.modul, request.user):
            return CustomResponse(success=False, message="Anda bukan pemilik modul dari jadwal ini", status=status.HTTP_403_FORBIDDEN )

        serializer = GroupScheduleSerializer(group, data=request.data, partial=True, context={'request':request})
        if serializer.is_valid():
            new_schedule = serializer.validated_data.get('schedule')
            if new_schedule and not self._check_user_ownership(new_schedule, request.user):
                return CustomResponse(success=False, message="Schedule baru tidak dimiliki oleh modul Anda", status=status.HTTP_403_FORBIDDEN )

            serializer.save()
            return CustomResponse(success=True, message="Group Schedule berhasil diperbarui", data=serializer.data)
        return CustomResponse(success=False, message="Validation failed", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id=None):
        group = get_object_or_404(GroupSchedule, id=id)
        if not self._check_user_ownership(group.modul, request.user):
            return CustomResponse(success=False, message="Anda bukan pemilik modul dari jadwal ini", status=status.HTTP_403_FORBIDDEN )
        group.delete()
        return CustomResponse(success=True, message="Group Schedule berhasil dihapus", status=status.HTTP_204_NO_CONTENT)
    
class ControlGroupScheduleView(APIView):
        permission_classes = [IsAuthenticated]

        def _check_user_ownership(self, modul, user):
            """Pastikan user adalah pemilik modul dari schedule"""
            if not modul.user.filter(id=user.id).exists():
                return False
            return True

        def get(self, request, id, control):
            group = get_object_or_404(GroupSchedule, id=id)
            pins = ModulePin.objects.filter(group=group)
            if not self._check_user_ownership(group.modul, request.user):
                return CustomResponse(success=False, message="Anda bukan pemilik modul dari jadwal ini", status=status.HTTP_403_FORBIDDEN )
            if control == 'on':
                pins.update(status=True)
            elif control == 'off':
                pins.update(status=False)
            else:
                return CustomResponse(success=False, message="Tidak mengontrol pin.")
            serializer = GroupScheduleSerializer(group)
            return CustomResponse(success=True, message="Detail group schedule", data=serializer.data)


class ListGroupAlarmAPIView(APIView):
    """
    View untuk mengambil list alarm di group (GET)
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, id, user):
        """
        Helper method untuk mengambil objek alaram.
        Memastikan objek ada dan dimiliki oleh pengguna yang benar.
        """
        try:
            return Alarm.objects.filter(group__id=id, group__modul__user=user)
        except Alarm.DoesNotExist:
            raise Http404

    def get(self, request, id):
        """Mengambil list alaram."""
        alarm = self.get_object(id, request.user)
        serializer = AlarmSerializer(alarm, many=True)
        return CustomResponse(data = serializer.data)