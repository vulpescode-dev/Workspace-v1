"""Formularios, al estilo de Google Forms: un formulario tiene preguntas en orden y recibe envíos.

Nombres elegidos para no chocar con Django ni DRF: ``DynamicForm`` (no ``Form``, que es
``django.forms.Form``) y ``Submission`` (no ``Response``, que es la respuesta HTTP de DRF/Django).

Borrado suave con ``deleted_at``, igual que las publicaciones: un formulario con envíos no se
pierde por un clic.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class DynamicForm(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Borrador"           # se está armando; nadie puede responder
        OPEN = "open", "Abierto"              # recibe envíos (dentro de opens_at / closes_at, si hay)
        CLOSED = "closed", "Cerrado"          # ya no recibe envíos; se conservan los que hay

    # Identificador para el enlace que se comparte (/forms/<uuid>/): no deja adivinar otros formularios.
    uuid = models.UUIDField("identificador público", default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField("título", max_length=200)
    description = models.TextField("descripción", max_length=2000, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="dynamic_forms", verbose_name="creado por"
    )
    status = models.CharField("estado", max_length=10, choices=Status.choices, default=Status.DRAFT)
    opens_at = models.DateTimeField("abre el", null=True, blank=True, help_text="Vacío: desde que se abre.")
    closes_at = models.DateTimeField("cierra el", null=True, blank=True, help_text="Vacío: hasta que se cierre a mano.")
    one_submission_per_user = models.BooleanField(
        "un envío por persona", default=True,
        help_text="Como «Limitar a 1 respuesta» de Google Forms.",
    )
    created_at = models.DateTimeField("creado el", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado el", auto_now=True)
    deleted_at = models.DateTimeField("eliminado el", null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = "formulario"
        verbose_name_plural = "formularios"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return self.title

    @property
    def is_accepting_submissions(self) -> bool:
        now = timezone.now()
        return (
            self.status == self.Status.OPEN and self.deleted_at is None
            and (self.opens_at is None or self.opens_at <= now)
            and (self.closes_at is None or now < self.closes_at)
        )

    def soft_delete(self) -> None:
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])
