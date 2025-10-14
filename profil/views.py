from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from smartfarming.utils.exc_handler import CustomResponse
from rest_framework.status import *

from .serializers import *

class ProfileAPIView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return CustomResponse(success=True, message="Autentifikasi tidak valid silahkan login ulang.", status=status.HTTP_401_UNAUTHORIZED)
        profil = get_object_or_404(UserProfile, user = request.user)
        serializer = ProfileSerializers(profil)
        return CustomResponse(data = serializer.data, status=HTTP_200_OK)
    
    def patch(self, request):
        if not request.user.is_authenticated:
            return CustomResponse(success=True, message="Autentifikasi tidak valid silahkan login ulang.", status=status.HTTP_401_UNAUTHORIZED)
        profil = get_object_or_404(UserProfile, user = request.user)
        serializer = ProfileSerializers(profil, data= request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(success=True, message="Profil berhasil diperbarui!", data=serializer.data, status=status.HTTP_200_OK)
        return CustomResponse(success=True, message="Format data yang dikirim tidak sesuai.", data=None, status=status.HTTP_400_BAD_REQUEST)