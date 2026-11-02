"""Reglas de django-allauth para Workspace: «Continuar con Google» solo para el personal.

- Solo cuentas de Google Workspace del dominio de la empresa (``GOOGLE_ALLOWED_DOMAIN``,
  @orienta.soy): se exige el dominio del correo, que Google lo marque como verificado y que la
  cuenta pertenezca a ese Workspace (``hd``). El parámetro ``hd`` que se manda a Google solo filtra
  su pantalla; la seguridad está aquí, en el servidor.
- La primera vez se crea la cuenta sola (nombre, correo y usuario a partir del correo); si ya
  existe alguien con ese correo, se entra a su cuenta y queda vinculada.
- No hay registro con contraseña desde la web: esas cuentas (bots, admin) las crea TI.
- Cualquier error o cancelación regresa al login con un mensaje (sin pantallas de allauth).
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.providers.base.constants import AuthError
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect


def allowed_domain() -> str:
    return settings.GOOGLE_ALLOWED_DOMAIN.lower().lstrip("@")


def _back_to_login(request, message: str):
    messages.error(request, message)
    raise ImmediateHttpResponse(redirect(settings.LOGIN_URL))


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False   # sin registro con contraseña; el personal entra con Google


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True    # ya se validó el dominio en pre_social_login

    def pre_social_login(self, request, sociallogin):
        domain = allowed_domain()
        data = sociallogin.account.extra_data or {}
        email = (data.get("email") or "").strip().lower()
        verified = bool(data.get("email_verified") or data.get("verified_email"))
        if not (email.endswith("@" + domain) and verified and (data.get("hd") or "").lower() == domain):
            _back_to_login(request, f"Usa tu cuenta de Google @{domain} para entrar.")
        user = sociallogin.user
        if user.pk and not user.is_active:
            _back_to_login(request, "Esta cuenta está desactivada. Contacta a Soporte TI.")

    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        if error == AuthError.CANCELLED:
            _back_to_login(request, "Cancelaste el inicio de sesión con Google.")
        _back_to_login(request, "No se pudo iniciar sesión con Google. Inténtalo de nuevo.")

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.email = (user.email or "").lower()
        return user
