"""Departamentos de la empresa.

Un departamento puede depender de otro (``parent``: Operaciones → Áreas Públicas) y tener un
responsable (``head``). Las personas se ligan con ``User.department``. Vive en ``accounts`` junto a
``User`` porque se apuntan entre sí (área y jefe): así la app tiene una sola migración inicial. Desactivar un
departamento lo saca de las listas, pero sus personas y tickets lo conservan.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower

DEPARTMENT_NAME_MAX_LENGTH = 120


class Department(models.Model):
    name = models.CharField("nombre", max_length=DEPARTMENT_NAME_MAX_LENGTH)
    description = models.CharField("descripción", max_length=300, blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="children", verbose_name="depende de",
    )
    head = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="headed_departments", verbose_name="responsable",
    )
    is_active = models.BooleanField("activo", default=True)
    created_at = models.DateTimeField("creado el", auto_now_add=True)

    class Meta:
        verbose_name = "departamento"
        verbose_name_plural = "departamentos"
        ordering = ["name"]
        constraints = [
            # «Sistemas» y «sistemas» son el mismo departamento.
            models.UniqueConstraint(Lower("name"), name="department_name_ci_unique"),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self):
        """Un departamento no puede depender de sí mismo ni de uno de sus propios subdepartamentos."""
        seen = {self.pk}
        parent = self.parent
        while parent is not None:
            if parent.pk in seen:
                raise ValidationError({"parent": "Ese departamento depende de este: se formaría un ciclo."})
            seen.add(parent.pk)
            parent = parent.parent
