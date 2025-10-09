from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/device/(?P<serial_id>[\w-]+)/$', consumers.DeviceAuthConsumer.as_asgi()),
    re_path(r'ws/device/unauth/(?P<device_id>[\w-]+)/$', consumers.DeviceConsumer.as_asgi()),
]