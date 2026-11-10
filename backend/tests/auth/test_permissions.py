"""Pruebas del sistema de roles y permisos con alcance (etapa 1)."""
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import Permission, Role, RolePermission, User, UserRole
from apps.accounts.services.permissions import has_permission, has_view_all


def make_user(username, *codenames, role_active=True, **extra):
    user = User.objects.create_user(username=username, email=f"{username}@example.test", password="x-Pass-12345", **extra)
    if codenames:
        role = Role.objects.create(name=f"rol-{username}", is_active=role_active)
        for code in codenames:
            perm, _ = Permission.objects.get_or_create(codename=code)
            RolePermission.objects.create(role=role, permission=perm)
        UserRole.objects.create(user=user, role=role)
    return user


class PermissionScopeTests(TestCase):
    def setUp(self):
        # Sin roles por defecto (Lector, Influencer…): aquí cada usuario tiene solo los permisos que se le den.
        Role.objects.update(is_default=False)

    def test_view_all_does_not_grant_modification_permissions(self):
        user = make_user("lector", "social.posts.view.all")
        self.assertTrue(has_view_all(user, "social.posts"))
        for code in ("social.posts.edit", "social.posts.delete", "social.posts.create"):
            self.assertFalse(has_permission(user, code), code)

    def test_view_all_is_per_resource(self):
        user = make_user("lector", "social.posts.view.all")
        self.assertFalse(has_view_all(user, "documents.documents"))

    def test_edit_permission_does_not_grant_view_all(self):
        user = make_user("editor", "social.posts.edit")
        self.assertTrue(has_permission(user, "social.posts.edit"))
        self.assertFalse(has_view_all(user, "social.posts"))

    def test_user_without_roles_has_no_permissions(self):
        user = make_user("sinrol")
        self.assertFalse(has_permission(user, "social.posts.create"))

    def test_multiple_roles_combine_permissions(self):
        user = make_user("multi", "social.posts.create")
        extra = Role.objects.create(name="auditor")
        perm, _ = Permission.objects.get_or_create(codename="social.posts.view.all")
        RolePermission.objects.create(role=extra, permission=perm)
        UserRole.objects.create(user=user, role=extra)
        self.assertTrue(has_permission(user, "social.posts.create"))
        self.assertTrue(has_view_all(user, "social.posts"))

    def test_inactive_role_grants_nothing(self):
        user = make_user("inactivo", "social.posts.view.all", role_active=False)
        self.assertFalse(has_view_all(user, "social.posts"))

    def test_inactive_user_and_anonymous_have_no_permissions(self):
        user = make_user("baja", "social.posts.view.all", is_active=False)
        self.assertFalse(has_view_all(user, "social.posts"))
        self.assertFalse(has_view_all(AnonymousUser(), "social.posts"))

    def test_superuser_has_all_permissions(self):
        admin = User.objects.create_superuser("root", "root@example.test", "x-Pass-12345")
        self.assertTrue(has_permission(admin, "social.posts.delete"))

    def test_duplicate_role_assignment_is_rejected(self):
        user = make_user("dup", "social.posts.create")
        role = user.roles.first()
        with self.assertRaises(IntegrityError), transaction.atomic():
            UserRole.objects.create(user=user, role=role)

    def test_email_is_unique(self):
        make_user("a")
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(username="b", email="a@example.test", password="x-Pass-12345")
