"""Estructura del proyecto: backend solo API, admin protegido, raíz /api/ sin versión y ajustes desde .env."""
import re

from django.conf import settings
from django.test import TestCase
from django.urls import Resolver404, resolve


class ProjectTests(TestCase):
    def test_admin_requires_login(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_api_root_lives_under_api_without_version(self):
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("social.posts", response.json()["endpoints"])
        self.assertEqual(self.client.get("/api/v1/").status_code, 404)

    def test_no_api_route_uses_version_prefix(self):
        for path in ("/api/v1/", "/api/v2/"):
            with self.assertRaises(Resolver404):
                resolve(path)

    def test_database_is_sqlite_and_custom_user_configured(self):
        self.assertEqual(settings.DATABASES["default"]["ENGINE"], "django.db.backends.sqlite3")
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")

    def test_csrf_middleware_enabled(self):
        self.assertIn("django.middleware.csrf.CsrfViewMiddleware", settings.MIDDLEWARE)

    def test_backend_only_serves_api_and_admin(self):
        for path in ("/", "/accounts/login/", "/people/", "/manifest.webmanifest"):
            with self.subTest(path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_project_identity_comes_from_env(self):
        self.assertTrue(settings.PROJECT_NAME)
        self.assertEqual(settings.PROJECT_CODE, settings.PROJECT_CODE.lower())
        self.assertEqual(self.client.get("/api/").json()["name"], f"{settings.PROJECT_NAME} API")
        self.assertEqual(settings.SIMPLE_JWT["ISSUER"], settings.PROJECT_CODE)
        self.assertTrue(settings.SESSION_COOKIE_NAME.startswith(settings.PROJECT_CODE))
