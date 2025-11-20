import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartfarming.settings')
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from smartfarming.middleware import JwtAuthMiddleware
import smartfarming.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JwtAuthMiddleware(
        URLRouter(
            smartfarming.routing.websocket_urlpatterns
        )
    ),
})