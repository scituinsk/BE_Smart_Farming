from django.urls import path
from .views import *

app_name = "iot"

urlpatterns = [
    path("control/", ControlDeviceView.as_view(), name="control-iot"),
    
    # admin
    path("admin/device/", DeviceListAdminView.as_view(), name="device-iot"),
    path("admin/device/<int:pk>/", DeviceDetailAdminView.as_view(), name="delete-device-iot"),

    # device
    path("device/<uuid:serial_id>/", ModulUserView.as_view(), name="device-detail"),
    path("device/list/", ModulListUserView.as_view(), name="device-list-by-user"),
    path('device/<uuid:serial_id>/qr/', ModulQRCodeView.as_view(), name='modul-qr-code'),

    # feature
    path("feature/", FeatureListView.as_view(), name="feature-list"),
    path("feature/<int:id>/", FeatureDetailView.as_view(), name="feature-detail"),


]
