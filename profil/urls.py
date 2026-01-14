from django.urls import path
from .views import *

app_name = "profil"

urlpatterns = [
    path('me', ProfileAPIView.as_view(), name='profile-me'),
    path('notifications', NotificationsAPIView.as_view(), name='list-notifications'),
    path('notification/read/<int:id>', NotificationsReadAPIView.as_view(), name='read'),
    path('notification/read-all', NotificationsReadAllView.as_view(), name='read-all')
]