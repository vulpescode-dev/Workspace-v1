"""Catálogo de permisos de negocio (apps/accounts/data/permissions.json)."""
import json
import re
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from apps.accounts.models import Permission, Role, RolePermission
from apps.accounts.services.permission_catalog import read_permissions_json, sync_permissions
from apps.accounts.services.role_catalog import RoleSeed, read_roles_json, sync_roles

CODENAME = re.compile(r"^[a-z][a-z_]*\.[a-z][a-z_]*\.[a-z][a-z_]*(\.all)?$")

# Los que ya usa el código: si alguien los renombra en el catálogo, esto avisa.
IN_USE = {
    "blog.articles.create", "documents.documents.create", "documents.documents.manage",
    "documents.documents.view.all", "forms.forms.create", "helpdesk.tickets.attend", "helpdesk.tickets.view.all",
}


def write_catalog(apps) -> Path:
    file = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump({"apps": apps}, file)
    file.close()
    return Path(file.name)


def catalog_with(actions: dict) -> Path:
    return write_catalog([{"code": "demo", "name": "Demo", "resources": [{"code": "things", "name": "Cosas", "actions": actions}]}])


class PermissionCatalogTests(TestCase):
    def test_catalog_is_valid_and_keeps_the_codes_in_use(self):
        catalog = read_permissions_json()
        self.assertTrue(all(CODENAME.match(code) for code in catalog), [c for c in catalog if not CODENAME.match(c)])
        self.assertLessEqual(IN_USE, set(catalog))
        self.assertFalse(any(text.startswith("★") for text in catalog.values()))

    def test_migrate_leaves_the_table_equal_to_the_catalog(self):
        self.assertEqual(set(Permission.objects.values_list("codename", flat=True)), set(read_permissions_json()))

    def test_sync_creates_and_updates_without_pruning(self):
        Permission.objects.create(codename="old.thing.view", description="Vieja")
        result = sync_permissions({"demo.things.view": "Ver", "old.thing.view": "Nueva descripción"})
        self.assertEqual((result.created, result.updated, result.deleted), (1, 1, 0))
        self.assertEqual(Permission.objects.get(codename="old.thing.view").description, "Nueva descripción")

    def test_prune_removes_stale_permissions_but_keeps_role_links_of_the_rest(self):
        role = Role.objects.create(name="Editor")
        keep = Permission.objects.get(codename="blog.articles.create")
        stale = Permission.objects.create(codename="old.thing.view")
        RolePermission.objects.create(role=role, permission=keep)
        RolePermission.objects.create(role=role, permission=stale)
        call_command("load_permissions", "--prune", stdout=open(tempfile.mktemp(), "w"))
        self.assertFalse(Permission.objects.filter(codename="old.thing.view").exists())
        self.assertEqual(list(role.permissions.values_list("codename", flat=True)), ["blog.articles.create"])

    def test_invalid_catalogs_are_rejected(self):
        for actions in ({"View": "Mal"}, {"view.todos": "Mal"}, {"view": ""}, {"view": "x" * 300}):
            with self.subTest(actions=actions), self.assertRaises(ValueError):
                read_permissions_json(catalog_with(actions))

    def test_duplicates_are_rejected(self):
        resource = {"code": "things", "name": "Cosas", "actions": {"view": "Ver"}}
        path = write_catalog([{"code": "demo", "name": "Demo", "resources": [resource, resource]}])
        with self.assertRaises(ValueError):
            read_permissions_json(path)


class RoleSeedTests(TestCase):
    """Roles básicos (apps/accounts/data/roles.json)."""

    def test_migrate_creates_the_basic_roles(self):
        reader = Role.objects.get(name="Lector")
        self.assertTrue(reader.is_default)
        codes = set(reader.permissions.values_list("codename", flat=True))
        self.assertIn("social.posts.view", codes)
        self.assertFalse(any(code.endswith(".all") for code in codes), "el Lector no debe ver lo ajeno")
        self.assertEqual(set(Role.objects.get(name="Blogger").permissions.values_list("codename", flat=True)),
                         {"blog.articles.view", "blog.articles.create"})

    def test_every_seed_permission_is_in_the_catalog(self):
        catalog = set(read_permissions_json())
        for seed in read_roles_json():
            self.assertLessEqual(set(seed.permissions), catalog, seed.name)

    def test_existing_roles_are_respected_unless_update(self):
        reader = Role.objects.get(name="Lector")
        reader.is_default = False
        reader.save()
        RolePermission.objects.filter(role=reader, permission__codename="forms.forms.view").delete()
        RolePermission.objects.create(role=reader, permission=Permission.objects.get(codename="social.posts.create"))

        self.assertEqual(sync_roles(read_roles_json()).created, 0)
        reader.refresh_from_db()
        self.assertFalse(reader.is_default)

        self.assertEqual(sync_roles(read_roles_json(), update=True).updated, len(read_roles_json()))
        reader.refresh_from_db()
        codes = set(reader.permissions.values_list("codename", flat=True))
        self.assertTrue(reader.is_default)
        self.assertIn("forms.forms.view", codes)
        self.assertNotIn("social.posts.create", codes)

    def test_unknown_permissions_stop_the_seed(self):
        seeds = [RoleSeed("Raro", "", False, ("no.existe.view",))]
        with self.assertRaises(ValueError):
            sync_roles(seeds)
        self.assertFalse(Role.objects.filter(name="Raro").exists())
