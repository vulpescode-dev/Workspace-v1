"""App instalable (PWA): manifest público con íconos que existen, enlazado en todas las páginas."""
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class ManifestTests(TestCase):
    def test_manifest_is_public_json_with_required_fields(self):
        response = self.client.get(reverse("manifest"))      # el navegador lo pide sin cookies
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/manifest+json")
        data = response.json()
        for field in ("name", "short_name", "start_url", "scope", "display", "theme_color", "background_color", "icons"):
            self.assertIn(field, data)
        self.assertEqual(data["display"], "standalone")
        self.assertEqual(data["start_url"], "/")
        sizes = {(icon["sizes"], icon["purpose"]) for icon in data["icons"]}
        self.assertTrue({("192x192", "any"), ("512x512", "any"), ("512x512", "maskable")} <= sizes)

    def test_icons_exist_on_disk(self):
        data = self.client.get(reverse("manifest")).json()
        icons = data["icons"] + [icon for shortcut in data["shortcuts"] for icon in shortcut["icons"]]
        for icon in icons:
            relative = icon["src"].split(settings.STATIC_URL, 1)[1].split("?", 1)[0]
            self.assertTrue(Path(settings.BASE_DIR, "static", relative).is_file(), icon["src"])

    def test_manifest_and_icons_linked_on_public_and_private_pages(self):
        login = self.client.get(reverse("accounts:login"))
        user = User.objects.create_user(username="ana", email="ana@example.test", password="x-Pass-12345")
        self.client.force_login(user)
        for response in (login, self.client.get(reverse("social:home")), self.client.get(reverse("people"))):
            self.assertContains(response, '<link rel="manifest" href="/manifest.webmanifest">')
            self.assertContains(response, 'rel="apple-touch-icon"')
            self.assertContains(response, "favicon.ico")
