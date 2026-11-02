"""Roles y permisos de negocio con alcance sobre registros.

Relación con las herramientas nativas de Django:
- La autenticación, sesiones y ``is_staff``/``is_superuser`` siguen siendo las de Django.
- El acceso al Django Admin sigue gobernado por los permisos nativos de Django.
- Los permisos de negocio (``Permission`` de este módulo) son independientes de
  ``django.contrib.auth.Permission`` y solo gobiernan las reglas de Workspace
  (p. ej. ``social.posts.view.all``). No se duplican mecanismos: no se
  sincronizan con los grupos de Django.
"""
from django.conf import settings
from django.db import models


class Role(models.Model):
    """Rol de negocio (no es un departamento ni un cargo laboral)."""

    name = models.CharField("nombre", max_length=80, unique=True)
    description = models.TextField("descripción", blank=True)
    permissions = models.ManyToManyField(
        "accounts.Permission",
        through="accounts.RolePermission",
        related_name="roles",
        blank=True,
        verbose_name="permisos",
    )
    is_active = models.BooleanField("activo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "rol"
        verbose_name_plural = "roles"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Permission(models.Model):
    """Permiso de negocio con nomenclatura ``app.recurso.accion[.alcance]``.

    Ejemplos: ``social.posts.create``, ``social.posts.view.all``.
    """

    codename = models.CharField("código", max_length=120, unique=True)
    description = models.CharField("descripción", max_length=255, blank=True)

    class Meta:
        verbose_name = "permiso de negocio"
        verbose_name_plural = "permisos de negocio"
        ordering = ["codename"]

    def __str__(self) -> str:
        return self.codename


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name="role_permissions"
    )

    class Meta:
        verbose_name = "permiso de rol"
        verbose_name_plural = "permisos de rol"
        constraints = [
            models.UniqueConstraint(fields=["role", "permission"], name="uniq_role_permission"),
        ]

    def __str__(self) -> str:
        return f"{self.role} → {self.permission}"


class UserRole(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_roles"
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "rol de usuario"
        verbose_name_plural = "roles de usuario"
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="uniq_user_role"),
        ]

    def __str__(self) -> str:
        return f"{self.user} → {self.role}"
