"""Biblioteca de documentos: categorías, documentos con privacidad y sus versiones.

- ``DocumentCategory``: «Políticas», «Formatos», «Manuales»… Las define la empresa en el admin.
- ``Document``: la ficha (título, descripción, categoría, dueño) y **quién lo ve** (``visibility``):
  toda la empresa, solo ciertos departamentos o solo ciertas personas. La regla se aplica en
  ``selectors.documents``.
- ``DocumentVersion``: cada archivo subido es una versión numerada (v1, v2…) con nota de qué cambió.
  Nunca se sobrescribe: la versión vigente es la más reciente (``Document.current_version``) y las
  anteriores quedan en el historial. Archivos validados con ``apps.core.uploads.check_document_upload``,
  guardados como ``documents/<document_id>/<version_id>.<ext>`` y entregados por una vista autorizada.
- Borrado suave del documento con ``deleted_at`` (sus versiones y archivos se conservan).
"""
from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

DOCUMENT_TITLE_MAX_LENGTH = 150
DOCUMENT_DESCRIPTION_MAX_LENGTH = 2000
VERSION_NOTES_MAX_LENGTH = 500


class DocumentCategory(models.Model):
    """Categoría de documentos. Desactivada: ya no se puede elegir ni filtrar; sus documentos la conservan."""

    name = models.CharField("nombre", max_length=80, unique=True)
    description = models.CharField("descripción", max_length=300, blank=True)
    position = models.PositiveSmallIntegerField("orden", default=0)
    is_active = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "categoría de documento"
        verbose_name_plural = "categorías de documentos"
        ordering = ["position", "name"]

    def __str__(self) -> str:
        return self.name


class Document(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Toda la empresa"
        DEPARTMENTS = "departments", "Departamentos"     # personas de los departamentos elegidos
        USERS = "users", "Personas"                      # solo las personas elegidas

    title = models.CharField("título", max_length=DOCUMENT_TITLE_MAX_LENGTH)
    description = models.TextField("descripción", max_length=DOCUMENT_DESCRIPTION_MAX_LENGTH, blank=True)
    category = models.ForeignKey(
        DocumentCategory, on_delete=models.PROTECT, related_name="documents", verbose_name="categoría",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="documents_owned", verbose_name="dueño(a)",
    )
    visibility = models.CharField("quién lo ve", max_length=12, choices=Visibility.choices, default=Visibility.PUBLIC)
    departments = models.ManyToManyField(
        "accounts.Department", blank=True, related_name="documents", verbose_name="departamentos",
        help_text="Solo cuenta si «Quién lo ve» es Departamentos.",
    )
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="documents_shared", verbose_name="personas",
        help_text="Solo cuenta si «Quién lo ve» es Personas.",
    )
    current_version = models.OneToOneField(
        "DocumentVersion", on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
        verbose_name="versión vigente",
    )
    created_at = models.DateTimeField("creado el", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("actualizado el", auto_now=True)
    deleted_at = models.DateTimeField("eliminado el", null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = "documento"
        verbose_name_plural = "documentos"
        ordering = ["-updated_at", "-id"]
        indexes = [models.Index(fields=["category", "-updated_at"], name="document_category_updated_idx")]

    def __str__(self) -> str:
        return self.title


def version_file_path(instance, filename: str) -> str:
    # ``filename`` ya llega como "<id>.<ext>" desde services.documents.
    return f"documents/{instance.document_id}/{filename}"


class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="versions", verbose_name="documento")
    number = models.PositiveIntegerField("versión")
    notes = models.CharField("qué cambió", max_length=VERSION_NOTES_MAX_LENGTH, blank=True)
    file = models.FileField("archivo", upload_to=version_file_path, max_length=255, blank=True)
    original_name = models.CharField("nombre original", max_length=255, blank=True)
    content_type = models.CharField("tipo MIME", max_length=100)
    size = models.PositiveBigIntegerField("tamaño (bytes)")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="document_versions", verbose_name="subida por",
    )
    created_at = models.DateTimeField("subida el", auto_now_add=True)

    class Meta:
        verbose_name = "versión de documento"
        verbose_name_plural = "versiones de documentos"
        ordering = ["-number"]
        constraints = [models.UniqueConstraint(fields=["document", "number"], name="document_version_unique_number")]

    def __str__(self) -> str:
        return f"{self.document} · v{self.number}"


@receiver(post_delete, sender=DocumentVersion)
def _delete_version_file(sender, instance, **kwargs):
    """Al borrar el registro (o su documento) se borra también el archivo del disco."""
    if instance.file:
        instance.file.delete(save=False)
