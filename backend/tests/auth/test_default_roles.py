"""Roles por defecto (``Role.is_default``): se asignan solos a cada usuario nuevo."""
from django.test import TestCase

from apps.accounts.models import Permission, Role, RolePermission, User, UserRole
from apps.accounts.services.permissions import has_permission
from apps.accounts.services.roles import assign_role_to_all_users


def make_user(username, **extra):
    return User.objects.create_user(username=username, email=f"{username}@example.test", password="x-Pass-12345", **extra)


def roles_of(user):
    return set(UserRole.objects.filter(user=user).values_list("role__name", flat=True))


class DefaultRolesTests(TestCase):
    def setUp(self):
        Role.objects.all().delete()   # sin los roles semilla (p. ej. «Lector»): estas pruebas definen los suyos
        self.basic = Role.objects.create(name="Básico", is_default=True)
        RolePermission.objects.create(role=self.basic, permission=Permission.objects.get_or_create(codename="social.posts.create")[0])
        self.extra = Role.objects.create(name="Extra", is_default=True)
        Role.objects.create(name="Normal")
        Role.objects.create(name="Apagado", is_default=True, is_active=False)

    def test_new_user_gets_every_active_default_role(self):
        user = make_user("nuevo")
        self.assertEqual(roles_of(user), {"Básico", "Extra"})
        self.assertTrue(has_permission(user, "social.posts.create"))

    def test_superusers_created_from_the_console_also_get_them(self):
        admin = User.objects.create_superuser(username="jefa", email="jefa@example.test", password="x-Pass-12345")
        self.assertEqual(roles_of(admin), {"Básico", "Extra"})

    def test_saving_an_existing_user_does_not_reassign_removed_roles(self):
        user = make_user("nuevo")
        UserRole.objects.filter(user=user, role=self.extra).delete()
        user.first_name = "Cambio"
        user.save()
        self.assertEqual(roles_of(user), {"Básico"})

    def test_marking_a_role_default_later_does_not_touch_existing_users(self):
        user = make_user("antes")
        late = Role.objects.create(name="Tardío")
        late.is_default = True
        late.save()
        self.assertNotIn("Tardío", roles_of(user))

    def test_assign_to_all_users_fills_only_active_users_missing_it(self):
        late = Role.objects.create(name="Tardío")
        has_it = make_user("ya")
        UserRole.objects.create(user=has_it, role=late)
        missing = make_user("falta")
        inactive = make_user("baja", is_active=False)
        self.assertEqual(assign_role_to_all_users(late), 1)
        self.assertIn("Tardío", roles_of(missing))
        self.assertNotIn("Tardío", roles_of(inactive))
        self.assertEqual(assign_role_to_all_users(late), 0)   # repetirlo no duplica

    def test_without_default_roles_nothing_is_assigned(self):
        Role.objects.update(is_default=False)
        self.assertEqual(roles_of(make_user("solo")), set())
