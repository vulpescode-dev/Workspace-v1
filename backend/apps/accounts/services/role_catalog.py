"""Roles básicos de partida: ``apps/accounts/data/roles.json``.

- En cada ``migrate`` se crean los roles que no existan (se buscan por nombre) con sus permisos. Los que
  ya existen no se tocan: lo que se cambie en el admin (permisos, descripción, «por defecto») se respeta.
- ``manage.py load_roles --update`` los deja otra vez exactamente como en el JSON.
- Cada permiso debe existir en el catálogo de permisos; si no, se detiene con ``ValueError``.
"""
import json
from dataclasses import dataclass
from pathlib import Path

from django.db import transaction

DEFAULT_ROLES_JSON = Path(__file__).resolve().parent.parent / "data" / "roles.json"


@dataclass(frozen=True)
class RoleSeed:
    name: str
    description: str
    is_default: bool
    permissions: tuple[str, ...]


@dataclass(frozen=True)
class RoleSyncResult:
    created: int
    updated: int


def read_roles_json(path: Path = DEFAULT_ROLES_JSON) -> list[RoleSeed]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    seeds, names = [], set()
    for item in data["roles"]:
        name = item["name"].strip()
        if not name or name in names:
            raise ValueError(f"Nombre de rol vacío o repetido: {name!r}")
        names.add(name)
        seeds.append(RoleSeed(name, item.get("description", ""), bool(item.get("is_default", False)), tuple(item["permissions"])))
    return seeds


def sync_roles(seeds: list[RoleSeed], *, update: bool = False, using: str = "default") -> RoleSyncResult:
    """Crea los roles que falten. Con ``update`` también deja los existentes igual que el JSON
    (descripción, «por defecto» y exactamente esos permisos)."""
    from apps.accounts.models import Permission, Role, RolePermission

    wanted = {code for seed in seeds for code in seed.permissions}
    permissions = {p.codename: p for p in Permission.objects.using(using).filter(codename__in=wanted)}
    missing = wanted - set(permissions)
    if missing:
        raise ValueError(f"Permisos que no están en el catálogo: {', '.join(sorted(missing))}")

    created = updated = 0
    with transaction.atomic(using=using):
        for seed in seeds:
            role = Role.objects.using(using).filter(name=seed.name).first()
            if role is not None and not update:
                continue
            if role is None:
                role = Role.objects.using(using).create(name=seed.name, description=seed.description, is_default=seed.is_default)
                created += 1
            else:
                role.description, role.is_default = seed.description, seed.is_default
                role.save(update_fields=["description", "is_default"])
                RolePermission.objects.using(using).filter(role=role).exclude(permission__codename__in=seed.permissions).delete()
                updated += 1
            RolePermission.objects.using(using).bulk_create(
                [RolePermission(role=role, permission=permissions[code]) for code in seed.permissions], ignore_conflicts=True,
            )
    return RoleSyncResult(created, updated)
