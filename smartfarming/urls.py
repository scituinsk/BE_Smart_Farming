from django.contrib import admin
from django.urls import path, include
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf.urls.static import static
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from smartfarming.utils.permissions import IsSwaggerAllowed
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet

schema_view = get_schema_view(
    openapi.Info(
        title="Teknohole API",
        default_version='v1',
        description="Dokumentasi REST API Teknohole",
        contact=openapi.Contact(email="teknohole@gmail.com"),
    ),
    public=True,
    permission_classes=[IsSwaggerAllowed],
    authentication_classes=[SessionAuthentication],
)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet

fcm_router = DefaultRouter()
# digunakan mobile app untuk POST token
fcm_router.register(r'devices', FCMDeviceAuthorizedViewSet)

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html')),
    path('admin/', admin.site.urls),
    path('api/login', LoginView.as_view(), name='login'),
    path('api/logout', LogoutView.as_view(), name='logout'),
    path('api/register', RegistrationView.as_view(), name='register'),
    path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/reset-password', ResetPasswordView.as_view(), name='reset_password'),

    path('api/iot/', include('iot.urls')),
    path('api/profile/', include('profil.urls')),
    path('api/schedule/', include('schedule.urls')),
    path('api/', include(fcm_router.urls)),

    # Dokumentasi Swagger & Redoc
    path('api/doc/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)