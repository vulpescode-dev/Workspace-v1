"""Pruebas de /api/health/: abierta, 200/503 según las comprobaciones y detalle solo para personal."""
from unittest import mock

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User

HEALTH_URL = "/api/health/"


class HealthApiTests(TestCase):
    def test_open_without_session_and_minimal(self):
        response = APIClient().get(HEALTH_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(set(response.data["checks"]), {"database", "migrations", "storage", "catalogs"})
        self.assertNotIn("details", response.data)
        self.assertNotIn("environment", response.data)
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_staff_gets_details(self):
        staff = User.objects.create_user(username="ti", email="ti@example.test", password="x-Pass-12345", is_staff=True)
        client = APIClient()
        client.force_authenticate(staff)
        data = client.get(HEALTH_URL).data
        self.assertEqual(data["details"]["migrations"]["pending"], [])
        self.assertIn("apps.social", data["apps"])
        self.assertIn("django", data["environment"])

    def test_regular_user_does_not_get_details(self):
        user = User.objects.create_user(username="ana", email="ana@example.test", password="x-Pass-12345")
        client = APIClient()
        client.force_authenticate(user)
        self.assertNotIn("details", client.get(HEALTH_URL).data)

    def test_database_down_returns_503(self):
        with mock.patch.dict("apps.core.health.CHECKS", {"database": lambda: (False, {"error": "caída"})}):
            response = APIClient().get(HEALTH_URL)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["status"], "error")
        self.assertEqual(response.data["checks"]["database"], "error")
        self.assertEqual(response.data["checks"]["catalogs"], "error")   # depende de la base: ni se intenta
