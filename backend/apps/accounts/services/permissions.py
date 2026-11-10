"""Comprobación centralizada de permisos de negocio.

Separación de conceptos (ver AGENT.md):
- Permiso funcional: ¿puede el usuario realizar la operación? (``has_permission``)
- Alcance ``view.all``: ¿puede consultar todos los registros? (``has_view_all``)
- Visibilidad por audiencia: la aplican los selectores de cada app.
``view.all`` NO concede editar, eliminar, descargar ni administrar.
"""
from apps.accounts.models import Permission

VIEW_ALL_SUFFIX = ".view.all"


def user_permission_codenames(user) -> frozenset[str]:
    """Códigos de permisos de negocio del usuario (cacheado por instancia)."""
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return frozenset()
    cached = getattr(user, "_ws_perm_cache", None)
    if cached is None:
        cached = frozenset(
            Permission.objects.filter(
                role_permissions__role__is_active=True,
                role_permissions__role__user_roles__user=user,
            ).values_list("codename", flat=True)
        )
        user._ws_perm_cache = cached
    return cached


def has_permission(user, codename: str) -> bool:
    """Permiso funcional exacto. Un superusuario activo los tiene todos."""
    if getattr(user, "is_authenticated", False) and user.is_active and user.is_superuser:
        return True
    return codename in user_permission_codenames(user)


def require_permission(user, codename: str, message: str) -> None:
    """Corta la operación con ``PermissionDenied`` (la API responde 403 con ``message``) si el usuario
    no tiene el permiso. Para usar al inicio de cada servicio que crea algo."""
    from django.core.exceptions import PermissionDenied

    if not has_permission(user, codename):
        raise PermissionDenied(message)


def has_view_all(user, resource: str) -> bool:
    """¿Puede consultar todos los registros de ``resource`` (p. ej. 'social.posts')?"""
    return has_permission(user, f"{resource}{VIEW_ALL_SUFFIX}")
