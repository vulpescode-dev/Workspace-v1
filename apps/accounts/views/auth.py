from allauth.socialaccount.providers.google.views import oauth2_login
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods

from apps.accounts.forms.auth import LoginForm


class LoginView(DjangoLoginView):
    """Login con usuario/correo + contraseña y, si está configurado, «Continuar con Google»."""

    template_name = "pages/auth/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            google_enabled=settings.GOOGLE_LOGIN_ENABLED,
            # En desarrollo se ve el botón (deshabilitado) aunque falten las credenciales.
            google_pending=settings.DEBUG and not settings.GOOGLE_LOGIN_ENABLED,
            google_domain=settings.GOOGLE_ALLOWED_DOMAIN,
        )
        return context


@require_http_methods(["GET", "POST"])
def google_login(request):
    """Inicio de «Continuar con Google» (va antes que la ruta de allauth, misma URL).

    - Solo por POST con CSRF (el botón del login): un GET —un enlace o una imagen de otro sitio—
      no inicia el flujo y regresa al login en lugar de mostrar la pantalla de confirmación de allauth.
    - Sin credenciales configuradas, regresa al login con un aviso (en lugar de un error 500).
    """
    if not settings.GOOGLE_LOGIN_ENABLED:
        messages.error(request, "El inicio de sesión con Google todavía no está disponible.")
        return redirect(settings.LOGIN_URL)
    if request.method != "POST":
        return redirect(settings.LOGIN_URL)
    return oauth2_login(request)
