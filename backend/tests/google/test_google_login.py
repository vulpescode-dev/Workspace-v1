"""«Continuar con Google» (django-allauth): solo cuentas del Google Workspace de la empresa.

No hay conexión real con Google: se simula la respuesta que Google entrega tras el login y se
pasa por el mismo flujo de allauth (``complete_social_login``), con nuestras reglas del adaptador.
"""
from allauth.core import context
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase, override_settings

from apps.accounts.models import User

LOGIN_PAGE = "http://localhost:5173/login"   # login de React (FRONTEND_URL)

GOOGLE = {
    "GOOGLE_LOGIN_ENABLED": True,
    "SOCIALACCOUNT_PROVIDERS": {
        "google": {
            "APPS": [{"client_id": "test-client", "secret": "test-secret", "key": ""}],
            "SCOPE": ["profile", "email"],
            "AUTH_PARAMS": {"hd": "orienta.soy", "prompt": "select_account"},
            "EMAIL_AUTHENTICATION": True,
        }
    },
}


@override_settings(**GOOGLE, FRONTEND_URL="http://localhost:5173")
class GoogleLoginTests(TestCase):
    def google_login(self, email, *, hd="orienta.soy", verified=True, sub="1001", name=("Ana", "Ruiz")):
        """Simula volver de Google con estos datos. Devuelve (respuesta, request)."""
        request = RequestFactory().get("/accounts/google/login/callback/")
        SessionMiddleware(lambda r: None).process_request(request)
        request.session.save()
        MessageMiddleware(lambda r: None).process_request(request)
        request.user = AnonymousUser()
        data = {"sub": sub, "email": email, "email_verified": verified, "given_name": name[0], "family_name": name[1],
                "name": " ".join(name)}
        if hd:
            data["hd"] = hd
        with context.request_context(request):
            provider = get_adapter().get_provider(request, "google")
            login = provider.sociallogin_from_response(request, data)
            response = complete_social_login(request, login)
        return response, request

    def messages(self, request):
        return [str(m) for m in get_messages(request)]

    def test_first_login_creates_the_account(self):
        response, request = self.google_login("Ana.Ruiz@orienta.soy")
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="ana.ruiz@orienta.soy")
        self.assertEqual((user.first_name, user.last_name), ("Ana", "Ruiz"))
        self.assertTrue(user.username)
        self.assertFalse(user.has_usable_password())                       # entra con Google, no con contraseña
        self.assertEqual(request.user, user)
        self.assertTrue(SocialAccount.objects.filter(user=user, provider="google", uid="1001").exists())

    def test_existing_user_with_same_email_is_linked_not_duplicated(self):
        ana = User.objects.create_user(username="ana", email="ana.ruiz@orienta.soy", password="x-Pass-12345")
        response, request = self.google_login("ana.ruiz@orienta.soy")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(request.user, ana)
        self.assertEqual(User.objects.filter(email__iexact="ana.ruiz@orienta.soy").count(), 1)
        self.assertTrue(SocialAccount.objects.filter(user=ana, provider="google").exists())
        # Protección de allauth: al entrar por correo a una cuenta cuyo correo no se había verificado
        # en Workspace, su contraseña se desactiva (si alguien hubiera creado la cuenta con un correo
        # ajeno, pierde el acceso). De ahí en adelante entra con Google; TI puede poner otra contraseña.
        ana.refresh_from_db()
        self.assertFalse(ana.has_usable_password())

    def test_other_domains_and_unverified_emails_are_rejected(self):
        cases = {
            "gmail personal": dict(email="ana@gmail.com", hd=None),
            "otro Workspace": dict(email="ana@otraempresa.com", hd="otraempresa.com"),
            "correo de la empresa sin hd": dict(email="ana@orienta.soy", hd=None),
            "correo no verificado": dict(email="ana@orienta.soy", verified=False),
        }
        for label, kwargs in cases.items():
            with self.subTest(label):
                response, request = self.google_login(**kwargs)
                self.assertRedirects(response, LOGIN_PAGE, fetch_redirect_response=False)
                self.assertIn("Usa tu cuenta de Google @orienta.soy para entrar.", self.messages(request))
                self.assertFalse(request.user.is_authenticated)
        self.assertFalse(User.objects.exists())
        self.assertFalse(SocialAccount.objects.exists())

    def test_inactive_account_cannot_enter_with_google(self):
        User.objects.create_user(username="ana", email="ana@orienta.soy", password="x", is_active=False)
        response, request = self.google_login("ana@orienta.soy")
        self.assertRedirects(response, LOGIN_PAGE, fetch_redirect_response=False)
        self.assertFalse(request.user.is_authenticated)
