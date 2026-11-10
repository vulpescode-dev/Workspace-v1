"""Asignación de roles de negocio.

Roles por defecto (``Role.is_default``): cada usuario nuevo los recibe al crearse, venga de donde venga
(admin, inicio con Google, ``createsuperuser``, scripts), mediante la señal de ``apps.accounts.signals``.
Solo cuentan los roles activos. Marcar un rol como «por defecto» no lo agrega a los usuarios que ya
existen; para eso está ``assign_role_to_all_users`` (acción del admin).
"""
from apps.accounts.models import Role, User, UserRole


def default_roles():
    return Role.objects.filter(is_active=True, is_default=True)


def assign_default_roles(user) -> int:
    """Da a ``user`` los roles por defecto que aún no tenga. Devuelve cuántos se intentaron asignar."""
    roles = list(default_roles())
    UserRole.objects.bulk_create([UserRole(user=user, role=role) for role in roles], ignore_conflicts=True)
    _forget_permissions(user)
    return len(roles)


def assign_role_to_all_users(role: Role) -> int:
    """Asigna ``role`` a todos los usuarios activos que no lo tengan. Devuelve a cuántos se les agregó."""
    missing = list(User.objects.filter(is_active=True).exclude(user_roles__role=role).values_list("pk", flat=True))
    # ``ignore_conflicts``: si otro proceso lo asignó al mismo tiempo, no truena.
    UserRole.objects.bulk_create([UserRole(user_id=pk, role=role) for pk in missing], ignore_conflicts=True)
    return len(missing)


def _forget_permissions(user) -> None:
    # ``has_permission`` guarda en la instancia los permisos ya leídos: tras cambiar roles, que vuelva a leer.
    if hasattr(user, "_ws_perm_cache"):
        del user._ws_perm_cache
