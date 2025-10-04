from django.urls import path
from .views import *

app_name = "schedule"

urlpatterns = [
    path('alarms/', AlarmListCreateAPIView.as_view(), name='alarm-list-create'),
    path('alarms/<int:pk>/', AlarmDetailAPIView.as_view(), name='alarm-detail'),
]