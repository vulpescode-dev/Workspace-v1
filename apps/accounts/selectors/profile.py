"""Lectura de perfiles. Toda persona autenticada puede ver el perfil de cualquier empleado activo."""
from django.db.models import Q
from django.urls import reverse

from apps.accounts.models import User


def profile_user(viewer, user_id: int) -> User | None:
    """Usuario activo cuyo perfil puede ver ``viewer`` (``None`` si no existe o está inactivo)."""
    if not getattr(viewer, "is_authenticated", False) or not viewer.is_active:
        return None
    return User.objects.filter(pk=user_id, is_active=True).select_related("department", "manager").first()


def _image_url(user, field: str, route: str) -> str:
    """URL autorizada (nunca /media/) con versión para que el navegador no muestre la imagen vieja."""
    if not getattr(user, field):
        return ""
    version = int(user.profile_updated_at.timestamp() * 1000) if user.profile_updated_at else 0   # milisegundos
    return f"{reverse(route, kwargs={'pk': user.pk})}?v={version}"


def avatar_url(user) -> str:
    return _image_url(user, "avatar", "accounts-api:user-avatar")



def department_name(user) -> str:
    """Nombre del departamento de ``user`` («» si no tiene). Usar con ``select_related("department")``."""
    return user.department.name if user.department_id else ""


def initials(name: str) -> str:
    parts = [p for p in name.replace("_", " ").split() if p]
    return "".join(p[0] for p in parts[:2]).upper() or "?"


SEARCH_FIELDS = ("first_name", "last_name", "username", "email", "job_title", "department__name")


def directory(viewer, query: str = "", department_id: int | None = None, gender: str = "",
              marital_status: str = ""):
    """Personas activas para el directorio, por nombre. ``query`` busca en nombre, correo, cargo y departamento.

    Cada palabra debe aparecer en alguno de esos campos («ana ti» encuentra a Ana de TI).
    ``department_id``, ``gender`` y ``marital_status`` dejan solo a quienes coincidan (se combinan).
    """
    if not getattr(viewer, "is_authenticated", False) or not viewer.is_active:
        return User.objects.none()
    qs = User.objects.filter(is_active=True).select_related("department")
    if department_id:
        qs = qs.filter(department_id=department_id)
    if gender:
        qs = qs.filter(gender=gender)
    if marital_status:
        qs = qs.filter(marital_status=marital_status)
    for word in (query or "").split()[:5]:
        condition = Q()
        for field in SEARCH_FIELDS:
            condition |= Q(**{f"{field}__icontains": word})
        qs = qs.filter(condition)
    return qs.order_by("first_name", "last_name", "username", "id")
