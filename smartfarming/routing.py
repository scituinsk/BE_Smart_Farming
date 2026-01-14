from django.urls import re_path
from iot import consumers as iot
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/server/logs/$', consumers.LogConsumer.as_asgi()),
    re_path(r'ws/device/(?P<serial_id>[\w-]+)/$', iot.DeviceAuthConsumer.as_asgi()),
]