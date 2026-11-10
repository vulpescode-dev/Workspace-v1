"""JWT: login con usuario o correo, refresh en cookie httpOnly con rotación, logout que revoca y API con Bearer."""
from django.conf import settings
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User

LOGIN_URL = "/api/auth/login/"
REFRESH_URL = "/api/auth/refresh/"
LOGOUT_URL = "/api/auth/logout/"
ME_URL = "/api/accounts/me/"


class JwtAuthTests(TestCase):
    def setUp(self):
        cache.clear()   # el límite de intentos usa la caché
        self.client = APIClient()
        self.ana = User.objects.create_user(username="ana", email="Ana@orienta.soy", password="clave-segura-123")
        self.cookie = settings.JWT_REFRESH_COOKIE["key"]

    def login(self, username="ana", password="clave-segura-123"):
        return self.client.post(LOGIN_URL, {"username": username, "password": password}, format="json")

    def test_login_returns_access_and_sets_refresh_cookie(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {"access"})          # el refresh nunca va en el cuerpo
        cookie = response.cookies[self.cookie]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["path"], "/api/auth/")
        self.assertEqual(cookie["samesite"], settings.JWT_REFRESH_COOKIE["samesite"])

    def test_access_token_authenticates_the_api(self):
        access = self.login().json()["access"]
        self.assertEqual(APIClient().get(ME_URL).status_code, 401)
        api = APIClient()
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = api.get(ME_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.ana.pk)

    def test_login_with_email_case_insensitive(self):
        self.assertEqual(self.login(username="ANA@orienta.soy").status_code, 200)

    def test_wrong_password_unknown_account_and_inactive_get_same_generic_error(self):
        User.objects.create_user(username="beto", password="clave-segura-123", is_active=False)
        for identifier in ("ana", "ana@orienta.soy", "nadie", "nadie@orienta.soy", "beto"):
            with self.subTest(identifier=identifier):
                password = "mal" if identifier.startswith("ana") else "clave-segura-123"
                response = self.login(username=identifier, password=password)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json()["detail"], "Usuario o contraseña incorrectos.")
                self.assertNotIn(self.cookie, response.cookies)

    def test_refresh_rotates_cookie_and_old_one_is_revoked(self):
        self.login()
        old = self.client.cookies[self.cookie].value
        response = self.client.post(REFRESH_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        new = response.cookies[self.cookie].value
        self.assertNotEqual(old, new)

        replay = APIClient()
        replay.cookies[self.cookie] = old
        response = replay.post(REFRESH_URL)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.cookies[self.cookie].value, "")   # se borra la cookie inválida

    def test_refresh_without_cookie_is_401(self):
        self.assertEqual(self.client.post(REFRESH_URL).status_code, 401)

    def test_logout_revokes_refresh_and_clears_cookie(self):
        self.login()
        refresh = self.client.cookies[self.cookie].value
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.cookies[self.cookie].value, "")
        replay = APIClient()
        replay.cookies[self.cookie] = refresh
        self.assertEqual(replay.post(REFRESH_URL).status_code, 401)

    def test_logout_without_session_is_harmless(self):
        self.assertEqual(self.client.post(LOGOUT_URL).status_code, 204)

    def test_login_attempts_are_limited(self):
        limit = int(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["auth"].split("/")[0])
        statuses = [self.login(password="mal").status_code for _ in range(limit + 1)]
        self.assertEqual(statuses, [401] * limit + [429])
