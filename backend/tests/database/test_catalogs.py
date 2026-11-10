"""Pruebas del catálogo de emojis: carga desde JSON, archivos estáticos y API."""
import json
import tempfile
from io import StringIO
from pathlib import Path
from urllib.parse import urlsplit

from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.db.models import ProtectedError
from django.test import TestCase

from apps.accounts.models import User
from apps.catalogs.models import Emoji
from apps.catalogs.services.emojis import load_emojis, read_emojis_json
from apps.social.models import Post, PostReaction


class EmojiCatalogTests(TestCase):
    def test_migration_loads_full_catalog(self):
        items = read_emojis_json()
        self.assertGreater(len(items), 0)
        self.assertEqual(Emoji.objects.filter(is_active=True).count(), len(items))   # la migración carga todo el JSON
        self.assertEqual(Emoji.objects.first().code, "smile")

    def test_every_emoji_has_svg_and_lottie(self):
        for code in Emoji.objects.values_list("code", flat=True):
            for name in ("emoji.svg", "lottie.json"):
                self.assertIsNotNone(finders.find(f"assets/emoji/{code}/{name}"), f"{code}/{name}")

    def test_load_is_idempotent_and_deactivates_removed(self):
        out = StringIO()
        call_command("load_catalogs", stdout=out)
        self.assertIn("0 creados, 0 actualizados, 0 desactivados", out.getvalue())

        items = [i for i in read_emojis_json() if i["code"] != "rat"]
        items[0] = {**items[0], "label": "Sonrisa"}
        result = load_emojis(items)
        self.assertEqual((result.created, result.updated, result.deactivated), (0, 1, 1))
        self.assertFalse(Emoji.objects.get(code="rat").is_active)
        self.assertEqual(Emoji.objects.get(code="smile").label, "Sonrisa")

    def test_rejects_duplicate_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "emojis.json"
            path.write_text(json.dumps({"emojis": [read_emojis_json()[0]] * 2}), encoding="utf-8")
            with self.assertRaises(ValueError):
                read_emojis_json(path)

    def test_emoji_in_use_cannot_be_deleted(self):
        user = User.objects.create_user(username="ana", email="ana@example.test", password="x")
        post = Post.objects.create(author=user, body="hola")
        PostReaction.objects.create(post=post, user=user, emoji=Emoji.objects.get(code="joy"))
        with self.assertRaises(ProtectedError):
            Emoji.objects.get(code="joy").delete()

    def test_api_lists_catalog_with_asset_urls(self):
        Emoji.objects.filter(code="rat").update(is_active=False)
        response = self.client.get("/api/catalogs/emojis/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), len(read_emojis_json()))
        first = data[0]
        self.assertEqual(first["code"], "smile")
        # En desarrollo la URL lleva ?v=<versión> (apps/core/staticfiles.py): se compara solo la ruta.
        self.assertTrue(urlsplit(first["svg_url"]).path.endswith("/assets/emoji/smile/emoji.svg"))
        self.assertTrue(urlsplit(first["lottie_url"]).path.endswith("/assets/emoji/smile/lottie.json"))
        self.assertFalse(next(e for e in data if e["code"] == "rat")["is_active"])


class EmojiRecoveryTests(TestCase):
    """Recuperar los emojis si se pierden: ``load_catalogs`` y la red de seguridad de ``migrate``."""

    def test_load_catalogs_restores_emptied_emojis(self):
        Emoji.objects.all().delete()
        call_command("load_catalogs", stdout=StringIO())
        call_command("load_catalogs", stdout=StringIO())
        self.assertEqual(Emoji.objects.count(), len(read_emojis_json()))

    def test_post_migrate_restores_only_when_empty(self):
        from apps.catalogs.apps import _restore_emojis_if_empty

        Emoji.objects.filter(code="rat").update(is_active=False)
        _restore_emojis_if_empty(sender=None, using="default")
        self.assertFalse(Emoji.objects.get(code="rat").is_active)   # con datos, no toca nada (respeta el admin)

        Emoji.objects.all().delete()
        _restore_emojis_if_empty(sender=None, using="default")
        self.assertEqual(Emoji.objects.count(), len(read_emojis_json()))
