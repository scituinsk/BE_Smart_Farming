from django.http import Http404
from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from smartfarming.utils.exc_handler import CustomResponse
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
        alarms = Alarm.objects.filter(modul__user=request.user)
        serializer = AlarmSerializer(alarms, many=True)
        return CustomResponse(data = serializer.data)

    def post(self, request, format=None):
        """Membuat alaram baru untuk pengguna yang sedang login."""
        try :
            modul = get_object_or_404(Modul, id=request.data.get("modul"))
        except:
            return CustomResponse(message="Modul tidak ditemukan", status=status.HTTP_404_NOT_FOUND)

        if not modul.user.filter(username__iexact=request.user.username).exists():
            return CustomResponse(message="Anda tidak mempunyai modul ini", status=status.HTTP_403_FORBIDDEN)
        
        # Cek apakah modul memiliki feature bernama 'penjadwalan'
        if not modul.feature.filter(name__iexact='penjadwalan').exists():
            return CustomResponse(message="Modul ini tidak memiliki fitur 'penjadwalan'.", data=None, status=status.HTTP_403_FORBIDDEN)
        
        serializer = AlarmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save() 
            return CustomResponse(message="Alaram berhasil ditambahkan.",data = serializer.data, status=status.HTTP_201_CREATED)
        return CustomResponse(message="Masukkan dengan format (HH:MM:SS).", data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AlarmDetailAPIView(APIView):
    """
    View untuk mengambil (GET), memperbarui (PUT), atau menghapus (DELETE) 
    satu instance alaram.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        """
        Helper method untuk mengambil objek alaram.
        Memastikan objek ada dan dimiliki oleh pengguna yang benar.
        """
        try:
            return Alarm.objects.get(pk=pk, modul__user=user)
        except Alarm.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """Mengambil detail satu alaram."""
        alarm = self.get_object(pk, request.user)
        serializer = AlarmSerializer(alarm)
        return CustomResponse(data = serializer.data)

    def put(self, request, pk, format=None):
        """Memperbarui satu alaram."""
        alarm = self.get_object(pk, request.user)
        serializer = AlarmSerializer(alarm, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(data = serializer.data)
        return CustomResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Menghapus satu alaram."""
        alarm = self.get_object(pk, request.user)
        alarm.delete()
        return CustomResponse(message="Alaram berhasil dihapus.",status=status.HTTP_200_OK)
    
class LogsListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, serial_id):
        """Mengambil detail log modul."""
        modul = get_object_or_404(Modul, serial_id=serial_id)
        is_member = modul.user.filter(pk=request.user.pk).exists()

        if not is_member:
            return CustomResponse(message="Anda tidak memiliki izin untuk melihat log modul ini.", status=status.HTTP_403_FORBIDDEN)
        logs = ScheduleLog.objects.filter(modul = modul)
        serializer = ScheduleLogSerializer(logs, many=True)
        return CustomResponse(data = serializer.data, status=status.HTTP_200_OK)
    
class LogsDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        """
        Menghapus satu entitas log berdasarkan ID-nya.
        """
        log_object = get_object_or_404(ScheduleLog, id=id)
        is_member = log_object.modul.user.filter(pk=request.user.pk).exists()

        if not is_member:
            return CustomResponse(message="Anda tidak memiliki izin untuk menghapus log ini.", status=status.HTTP_403_FORBIDDEN)
        log_object.delete()
        return CustomResponse(message="Log berhasil dihapus.", status=status.HTTP_200_OK)