"""Operaciones que crean o modifican documentos y sus versiones.

Reglas (las mismas para la API y para futuras vistas; quién puede, en ``selectors.documents``):

- Subir un documento: ``documents.documents.create``. Nace con su archivo como **v1**.
- Ficha y privacidad (título, descripción, categoría, quién lo ve): su dueño o ``manage``.
  «Departamentos» exige al menos un departamento activo; «Personas», al menos una persona activa.
- **Nueva versión**: sube otro archivo; queda como vigente con el número siguiente. Nada se sobrescribe.
- **Restaurar** una versión anterior: se copia como versión nueva («Restaurada de la v2»), así el
  historial nunca se reescribe y siempre se sabe quién la regresó y cuándo.
- Eliminar: borrado suave (``deleted_at``); versiones y archivos se conservan.
- Archivos validados con ``check_document_upload`` (PDF, Office sin macros, imágenes, CSV/TXT; máx. 20 MB).
"""
from pathlib import Path

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.accounts.models import User
from apps.core.uploads import KIND_DOCUMENT, CheckedUpload, check_document_upload
from apps.documents.models import (
    DOCUMENT_DESCRIPTION_MAX_LENGTH, DOCUMENT_TITLE_MAX_LENGTH, VERSION_NOTES_MAX_LENGTH, Document, DocumentVersion,
)
from apps.documents.selectors.documents import active_categories, can_create, can_manage
from apps.accounts.models import Department

UNSET = object()   # al editar: distingue «no se mandó» de «se mandó vacío»
Visibility = Document.Visibility


def _clean_title(title: str) -> str:
    title = " ".join((title or "").split())
    if not title:
        raise ValidationError({"title": "Escribe un título."})
    if len(title) > DOCUMENT_TITLE_MAX_LENGTH:
        raise ValidationError({"title": f"Máximo {DOCUMENT_TITLE_MAX_LENGTH} caracteres."})
    return title


def _clean_text(text: str, field: str, max_length: int) -> str:
    # Los formularios multipart mandan los saltos de línea como CRLF: se guardan como LF.
    text = (text or "").replace("\r\n", "\n").strip()
    if len(text) > max_length:
        raise ValidationError({field: f"Máximo {max_length} caracteres."})
    return text


def _category(category_id):
    category = active_categories().filter(pk=category_id).first() if category_id else None
    if category is None:
        raise ValidationError({"category": "Elige una categoría válida."})
    return category


def _audience(visibility: str, department_ids, user_ids) -> tuple[list, list]:
    """Valida «quién lo ve» y devuelve (departamentos, personas) a guardar; vacías si no aplican."""
    if visibility not in Visibility.values:
        raise ValidationError({"visibility": "Elige quién lo ve."})
    departments, users = [], []
    if visibility == Visibility.DEPARTMENTS:
        ids = set(department_ids or [])
        departments = list(Department.objects.filter(pk__in=ids, is_active=True))
        if not departments or len(departments) != len(ids):
            raise ValidationError({"departments": "Elige al menos un departamento válido."})
    elif visibility == Visibility.USERS:
        ids = set(user_ids or [])
        users = list(User.objects.filter(pk__in=ids, is_active=True))
        if not users or len(users) != len(ids):
            raise ValidationError({"users": "Elige al menos una persona válida."})
    return departments, users


def _check_file(upload):
    if upload is None:
        raise ValidationError({"file": "Adjunta el archivo."})
    try:
        return check_document_upload(upload)
    except ValidationError as exc:
        raise ValidationError({"file": exc.messages[0]}) from exc


def _save_version(document: Document, user, *, content, name: str, info, notes: str) -> DocumentVersion:
    """Crea la versión siguiente, guarda su archivo y la deja vigente. Llamar dentro de una transacción."""
    # Bloquea el documento: dos subidas al mismo tiempo no pueden tomar el mismo número.
    Document.objects.select_for_update().filter(pk=document.pk).first()
    number = (document.versions.aggregate(last=Max("number"))["last"] or 0) + 1
    version = DocumentVersion.objects.create(
        document=document, number=number, notes=notes, uploaded_by=user,
        original_name=(name or "")[:255], content_type=info.content_type, size=info.size,
    )
    version.file.save(f"{version.pk}{info.extension}", content, save=True)
    document.current_version = version
    document.save(update_fields=["current_version", "updated_at"])
    return version


def create_document(
    *, owner, title: str, category_id, file, description: str = "", visibility: str = Visibility.PUBLIC,
    department_ids=(), user_ids=(), notes: str = "",
) -> Document:
    if not can_create(owner):
        raise PermissionDenied("No tienes permiso para subir documentos.")
    title = _clean_title(title)
    description = _clean_text(description, "description", DOCUMENT_DESCRIPTION_MAX_LENGTH)
    category = _category(category_id)
    departments, users = _audience(visibility, department_ids, user_ids)
    notes = _clean_text(notes, "notes", VERSION_NOTES_MAX_LENGTH)
    info = _check_file(file)

    with transaction.atomic():
        document = Document.objects.create(
            title=title, description=description, category=category, owner=owner, visibility=visibility,
        )
        document.departments.set(departments)
        document.shared_with.set(users)
        _save_version(document, owner, content=file, name=getattr(file, "name", ""), info=info,
                      notes=notes or "Versión inicial")
    return document


def _ensure_can_manage(user, document: Document) -> None:
    if not can_manage(user, document):
        raise PermissionDenied("Solo su dueño o quien administra documentos puede cambiarlo.")


def update_document(
    *, user, document: Document, title=UNSET, description=UNSET, category_id=UNSET, visibility=UNSET,
    department_ids=UNSET, user_ids=UNSET,
) -> Document:
    """Cambia solo lo que se mande. Al cambiar la privacidad, las listas que no aplican se vacían."""
    _ensure_can_manage(user, document)
    if title is not UNSET:
        document.title = _clean_title(title)
    if description is not UNSET:
        document.description = _clean_text(description, "description", DOCUMENT_DESCRIPTION_MAX_LENGTH)
    if category_id is not UNSET:
        document.category = _category(category_id)
    audience_changed = any(value is not UNSET for value in (visibility, department_ids, user_ids))
    if audience_changed:
        if visibility is not UNSET:
            document.visibility = visibility
        if department_ids is UNSET:
            department_ids = document.departments.values_list("pk", flat=True)
        if user_ids is UNSET:
            user_ids = document.shared_with.values_list("pk", flat=True)
        departments, users = _audience(document.visibility, department_ids, user_ids)

    with transaction.atomic():
        document.save()
        if audience_changed:
            document.departments.set(departments)
            document.shared_with.set(users)
    return document


def add_version(*, user, document: Document, file, notes: str = "") -> DocumentVersion:
    """Sube un archivo nuevo como la siguiente versión vigente."""
    _ensure_can_manage(user, document)
    notes = _clean_text(notes, "notes", VERSION_NOTES_MAX_LENGTH)
    info = _check_file(file)
    with transaction.atomic():
        return _save_version(document, user, content=file, name=getattr(file, "name", ""), info=info, notes=notes)


def restore_version(*, user, document: Document, version: DocumentVersion) -> DocumentVersion:
    """Regresa una versión anterior copiándola como versión nueva (el historial no se reescribe)."""
    _ensure_can_manage(user, document)
    if version.document_id != document.pk:
        raise ValidationError({"version": "Esa versión no es de este documento."})
    if document.current_version_id == version.pk:
        raise ValidationError({"version": "Esa ya es la versión vigente."})
    if not version.file:
        raise ValidationError({"version": "El archivo de esa versión ya no existe."})
    with version.file.open("rb") as source:
        content = ContentFile(source.read())
    # Ya se validó al subirla: se reutiliza lo que se sabe de ella (mismo tipo, tamaño y extensión).
    extension = Path(version.file.name).suffix
    info = CheckedUpload(kind=KIND_DOCUMENT, extension=extension, content_type=version.content_type, size=version.size)
    with transaction.atomic():
        return _save_version(document, user, content=content, name=version.original_name, info=info,
                             notes=f"Restaurada de la v{version.number}")


def delete_document(*, user, document: Document) -> None:
    _ensure_can_manage(user, document)
    document.deleted_at = timezone.now()
    document.save(update_fields=["deleted_at", "updated_at"])
