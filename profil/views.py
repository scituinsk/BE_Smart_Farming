from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from smartfarming.utils.exc_handler import CustomResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import *

from profil.serializers import *
from profil.models import *

class ProfileAPIView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return CustomResponse(success=True, message="Autentifikasi tidak valid silahkan login ulang.", status=status.HTTP_401_UNAUTHORIZED, request=request)
        profil = get_object_or_404(UserProfile, user = request.user)
        serializer = ProfileSerializers(profil)
        return CustomResponse(data = serializer.data, status=HTTP_200_OK, request=request)
    
    def patch(self, request):
        if not request.user.is_authenticated:
            return CustomResponse(success=True, message="Autentifikasi tidak valid silahkan login ulang.", status=status.HTTP_401_UNAUTHORIZED, request=request)
        profil = get_object_or_404(UserProfile, user = request.user)
        serializer = ProfileSerializers(profil, data= request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(success=True, message="Profil berhasil diperbarui!", data=serializer.data, status=status.HTTP_200_OK, request=request)
        return CustomResponse(success=True, message="Format data yang dikirim tidak sesuai.", data=None, status=status.HTTP_400_BAD_REQUEST, request=request)
    
class NotificationsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notif = Notification.objects.filter(user = request.user).order_by("-created_at")
        serializer = NotificationSerializers(notif, many=True)
        return CustomResponse(success=True, status=status.HTTP_200_OK,message="List Notifications", data=serializer.data, request=request)
    
class NotificationsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        notif = Notification.mark_as_read(id = id, user = request.user)
        serializer = NotificationSerializers(notif)
        return CustomResponse(success=True, status=status.HTTP_200_OK,message="Read Notifications", data=serializer.data, request=request)
    def delete(self, request, id):
        notif = get_object_or_404(Notification, id=id)
        if notif.user == request.user:
            notif.delete()
            return CustomResponse(success=True,message="Notifikasi berhasil dihapus", status=status.HTTP_204_NO_CONTENT, request=request)
        return CustomResponse(success=False,message="Notifikasi gagal dihapus", status=status.HTTP_401_UNAUTHORIZED, request=request)
    
class NotificationsReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        notif = Notification.mark_all_as_read(user = request.user)
        serializer = NotificationSerializers(notif, many=True)
        return CustomResponse(success=True, status=status.HTTP_200_OK,message="Read All Notifications", data=serializer.data, request=request)
    
        
