from django.urls import path
from .views import *

app_name = "schedule"

urlpatterns = [
    path('log/<int:id>/delete/', LogsDeleteAPIView.as_view(), name='log-list'),
    path('<str:serial_id>/logs/', LogsListAPIView.as_view(), name='log-list'),
    path('alarms/', AlarmListCreateAPIView.as_view(), name='alarm-list-create'),
    path('alarms/<int:pk>/', AlarmDetailAPIView.as_view(), name='alarm-detail'),
    path('groups/', GroupScheduleView.as_view(), name='list-all-group'),
    path('groups/<int:id>/', GroupScheduleView.as_view(), name='detail-group'),
    path('groups/<int:id>/<str:control>', ControlGroupScheduleView.as_view(), name='detail-group'),
    path('groups/<int:id>/<str:control>', ControlGroupScheduleView.as_view(), name='detail-group'),
    path('group/<int:id>/alarms/', ListGroupAlarmAPIView.as_view(), name='list-group-alarm'),
]