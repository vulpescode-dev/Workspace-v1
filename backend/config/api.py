"""Raíz de la API: única base /api/ (sin versionado)."""
from django.conf import settings
from django.urls import include, path
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from apps.core.health import run_checks


class ApiRootView(APIView):
    """Lista los endpoints disponibles. Se agregan por etapa."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "name": f"{settings.PROJECT_NAME} API",
            "endpoints": {
                "auth.login": reverse("auth-api:login", request=request),
                "auth.refresh": reverse("auth-api:refresh", request=request),
                "auth.logout": reverse("auth-api:logout", request=request),
                "accounts.me": reverse("accounts-api:me", request=request),
                "blog.articles": reverse("blog-api:article-list", request=request),
                "catalogs.emojis": reverse("catalogs-api:emoji-list", request=request),
                "documents.documents": reverse("documents-api:document-list", request=request),
                "health": reverse("api-health", request=request),
                "helpdesk.tickets": reverse("helpdesk-api:ticket-list", request=request),
                "marketplace.listings": reverse("marketplace-api:listing-list", request=request),
                "notifications": reverse("notifications-api:list", request=request),
                "org.chart": reverse("org-api:chart", request=request),
                "org.departments": reverse("org-api:department-list", request=request),
                "social.posts": reverse("social-api:post-list", request=request),
            },
        })



class HealthView(APIView):
    """GET: salud de la app (base de datos, migraciones, archivos subidos, datos base).

    Abierta sin sesión para monitores y balanceadores: responde **200** si todo está bien y **503**
    si algo falla, solo con ``ok``/``error`` por comprobación. Al personal (``is_staff``) además le
    muestra detalles: tiempos, errores, migraciones pendientes, apps instaladas y versiones.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        report = run_checks(detailed=request.user.is_staff)
        report["time"] = timezone.localtime().isoformat()
        response = Response(report, status=200 if report["status"] == "ok" else 503)
        response["Cache-Control"] = "no-store"
        return response


urlpatterns = [
    path("", ApiRootView.as_view(), name="api-root"),
    path("health/", HealthView.as_view(), name="api-health"),
    path("auth/", include("apps.accounts.api.auth_urls")),
    path("accounts/", include("apps.accounts.api.urls")),
    path("blog/", include("apps.blog.api.urls")),
    path("catalogs/", include("apps.catalogs.api.urls")),
    path("documents/", include("apps.documents.api.urls")),
    path("forms/", include("apps.form_builder.api.urls")),
    path("helpdesk/", include("apps.helpdesk.api.urls")),
    path("marketplace/", include("apps.marketplace.api.urls")),
    path("notifications/", include("apps.notifications.api.urls")),
    path("org/", include("apps.accounts.api.org_urls")),   # departamentos y organigrama (modelo en accounts)
    path("social/", include("apps.social.api.urls")),
]
