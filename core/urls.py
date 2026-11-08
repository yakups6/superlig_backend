from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)
from api.views import app_view

urlpatterns = [
    # Canlı Mobil Uygulama Arayüzü (Web SPA & Mobil Simülatör)
    path('', app_view, name='app-home'),
    path('app/', app_view, name='app-ui'),

    path('admin/', admin.site.urls),

    # OpenAPI 3.0 Şema Dosyası
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI Dokümantasyonu
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-docs'),

    # ReDoc Dokümantasyon Arayüzü
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API Endpoint'leri
    path('api/', include('api.urls')),
]
