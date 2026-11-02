from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView

from apps.accounts.views import people, profile
from apps.accounts.views.auth import google_login
from apps.blog.views import blog
from apps.core.pages import calendar_page, help_page, privacy, showcase, terms
from apps.core.pwa import manifest
from apps.documents.views.pages import documents
from apps.form_builder.views.pages import forms_home
from apps.helpdesk.views import helpdesk
from apps.marketplace.views import marketplace
from apps.notifications.views import notifications
from apps.org.views import org_chart

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("config.api")),
    path("accounts/", include("apps.accounts.urls")),   # login y logout propios (van primero)
    # De allauth solo se usa «Continuar con Google»; sus demás pantallas (registro con contraseña,
    # recuperar contraseña, correos, conexiones) no se ofrecen: llevan al login.
    re_path(
        r"^accounts/(?:signup|password|email|confirm-email|reauthenticate|inactive|3rdparty/?$)",
        RedirectView.as_view(pattern_name="accounts:login"),
    ),
    path("accounts/google/login/", google_login),   # envoltura: solo POST y solo si está configurado
    path("accounts/", include("allauth.urls")),
    path("profile/", profile, name="profile"),
    path("people/", people, name="people"),
    path("people/org/", org_chart, name="org-chart"),
    path("notifications/", notifications, name="notifications"),
    path("calendar/", calendar_page, name="calendar"),
    path("blog/", blog, name="blog"),
    path("documents/", documents, name="documents"),
    path("forms/", forms_home, name="forms"),
    path("marketplace/", marketplace, name="marketplace"),
    path("helpdesk/", helpdesk, name="helpdesk"),
    path("help/", help_page, name="help"),
    path("manifest.webmanifest", manifest, name="manifest"),
    path("terms/", terms, name="terms"),
    path("privacy/", privacy, name="privacy"),
    path("", include("apps.social.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path("showcase/", showcase, name="showcase")]   # presentación (ver apps/core/pages.py)
