from django.urls import path
from .views import *

app_name = "iot"

urlpatterns = [
    path("control/", ControlDeviceView.as_view(), name="control-iot")
]
