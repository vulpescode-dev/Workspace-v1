"""Quién ve y quién administra cada documento.

- **Ver** un documento (y descargar cualquiera de sus versiones):
  - «Toda la empresa»: cualquier persona activa con sesión.
  - «Departamentos»: las personas cuyo departamento está en la lista (no incluye subdepartamentos).
  - «Personas»: solo las personas elegidas.
  - Siempre: su dueño, quien tenga ``documents.documents.manage`` y quien tenga
    ``documents.documents.view.all`` (solo consulta: no concede administrar).
- **Subir** documentos nuevos: ``documents.documents.create``.
- **Administrar** uno (editar ficha y privacidad, subir o restaurar versiones, eliminar): su dueño o
  ``documents.documents.manage``. Un superusuario tiene todos los permisos.
"""
from django.db.models import Q

from apps.accounts.services.permissions import has_permission, has_view_all
from apps.documents.models import Document, DocumentCategory, DocumentVersion

CREATE_PERMISSION = "documents.documents.create"
MANAGE_PERMISSION = "documents.documents.manage"
DOCUMENTS_RESOURCE = "documents.documents"


def _is_active(user) -> bool:
    return getattr(user, "is_authenticated", False) and user.is_active


def can_create(user) -> bool:
    return _is_active(user) and has_permission(user, CREATE_PERMISSION)


def can_manage_all(user) -> bool:
    return _is_active(user) and has_permission(user, MANAGE_PERMISSION)


def can_manage(user, document: Document) -> bool:
    return _is_active(user) and (document.owner_id == user.pk or can_manage_all(user))


def visible_documents(user):
    """Documentos vivos que ``user`` puede ver, con categoría, dueño y versión vigente."""
    if not _is_active(user):
        return Document.objects.none()
    qs = Document.objects.filter(deleted_at__isnull=True).select_related(
        "category", "owner", "current_version", "current_version__uploaded_by",
    )
    if can_manage_all(user) or has_view_all(user, DOCUMENTS_RESOURCE):
        return qs
    audience = (
        Q(visibility=Document.Visibility.PUBLIC)
        | Q(owner=user)
        | Q(visibility=Document.Visibility.USERS, shared_with=user)
    )
    if user.department_id:
        audience |= Q(visibility=Document.Visibility.DEPARTMENTS, departments=user.department_id)
    # Los M2M pueden repetir filas: se filtra por id para no duplicar ni perder el orden.
    return qs.filter(pk__in=Document.objects.filter(audience).values("pk"))


SCOPES = ("mine", "shared")


def filter_documents(qs, user, *, scope: str = "", category: int | None = None, query: str = ""):
    """Filtros de la lista. ``scope``: ``mine`` (soy dueño) o ``shared`` (compartidos conmigo por persona o
    departamento). ``query`` busca en título y descripción."""
    if scope == "mine":
        qs = qs.filter(owner=user)
    elif scope == "shared":
        shared = Q(visibility=Document.Visibility.USERS, shared_with=user)
        if user.department_id:
            shared |= Q(visibility=Document.Visibility.DEPARTMENTS, departments=user.department_id)
        qs = qs.filter(pk__in=Document.objects.filter(shared).values("pk")).exclude(owner=user)
    if category:
        qs = qs.filter(category_id=category)
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))
    return qs


def visible_version(user, pk: int) -> DocumentVersion | None:
    """Una versión se entrega si su documento es visible para ``user``."""
    version = DocumentVersion.objects.filter(pk=pk).first()
    if version is None or not visible_documents(user).filter(pk=version.document_id).exists():
        return None
    return version


def active_categories():
    return DocumentCategory.objects.filter(is_active=True)
