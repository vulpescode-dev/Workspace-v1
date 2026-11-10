"""Rutas del backend: solo API (/api/) y administración (/admin/). Las pantallas viven en frontend/ (React)."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = admin.site.site_title = f"{settings.PROJECT_NAME} · Administración"
admin.site.index_title = settings.PROJECT_NAME

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("config.api")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
