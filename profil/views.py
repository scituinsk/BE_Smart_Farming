from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from smartfarming.utils.exc_handler import CustomResponse
from rest_framework.status import *

from .serializers import *

class ProfileAPIView(APIView):
    def get(self, request):
        """Mengambil detail satu alaram."""
        alarm = get_object_or_404(UserProfile, user = request.user)
        serializer = ProfileSerializers(alarm)
        return CustomResponse(data = serializer.data, status=HTTP_200_OK)