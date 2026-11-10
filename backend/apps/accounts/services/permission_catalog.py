"""Catálogo de permisos de negocio: ``apps/accounts/data/permissions.json`` es la única fuente.

- Código: ``app.recurso.acción`` (p. ej. ``social.posts.create``); ``.all`` al final = sobre registros
  de otras personas (``social.posts.delete.all``).
- Se sincroniza solo en cada ``migrate`` (crea los nuevos y actualiza descripciones) y a mano con
  ``manage.py load_permissions``. ``--prune`` además borra los que ya no estén en el catálogo (y con
  ellos sus asignaciones a roles).
- Las migraciones de cada app ya no crean permisos.
"""
import json
import re
from dataclasses import dataclass
from pathlib import Path

from django.db import transaction

DEFAULT_PERMISSIONS_JSON = Path(__file__).resolve().parent.parent / "data" / "permissions.json"
CODE = re.compile(r"^[a-z][a-z_]*$")
ACTION = re.compile(r"^[a-z][a-z_]*(\.all)?$")
DESCRIPTION_MAX_LENGTH = 255


@dataclass(frozen=True)
class SyncResult:
    created: int
    updated: int
    deleted: int


def read_permissions_json(path: Path = DEFAULT_PERMISSIONS_JSON) -> dict[str, str]:
    """Lee el catálogo y lo valida. Devuelve ``{código: descripción}``. Falla con ``ValueError`` si algo
    está mal escrito (mejor detenerse que dejar permisos a medias)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    catalog: dict[str, str] = {}
    for app in data["apps"]:
        if not CODE.match(app["code"]):
            raise ValueError(f"Código de app no válido: {app['code']!r}")
        for resource in app["resources"]:
            if not CODE.match(resource["code"]):
                raise ValueError(f"Código de recurso no válido: {app['code']}.{resource['code']!r}")
            for action, description in resource["actions"].items():
                codename = f"{app['code']}.{resource['code']}.{action}"
                if not ACTION.match(action):
                    raise ValueError(f"Acción no válida: {codename!r}")
                if codename in catalog:
                    raise ValueError(f"Permiso repetido: {codename}")
                description = description.removeprefix("★").strip()
                if not description or len(description) > DESCRIPTION_MAX_LENGTH:
                    raise ValueError(f"Descripción vacía o de más de {DESCRIPTION_MAX_LENGTH} caracteres: {codename}")
                catalog[codename] = description
    return catalog


def sync_permissions(catalog: dict[str, str], *, prune: bool = False, using: str = "default") -> SyncResult:
    """Deja la tabla de permisos igual al catálogo: crea los que falten y actualiza descripciones.
    Con ``prune`` borra los que sobren. Nunca toca las asignaciones de permisos que sí siguen."""
    from apps.accounts.models import Permission

    created = updated = deleted = 0
    with transaction.atomic(using=using):
        existing = {p.codename: p for p in Permission.objects.using(using).all()}
        new = [Permission(codename=code, description=text) for code, text in catalog.items() if code not in existing]
        Permission.objects.using(using).bulk_create(new)
        created = len(new)
        changed = [p for code, p in existing.items() if code in catalog and p.description != catalog[code]]
        for permission in changed:
            permission.description = catalog[permission.codename]
        Permission.objects.using(using).bulk_update(changed, ["description"])
        updated = len(changed)
        if prune:
            stale = [code for code in existing if code not in catalog]
            Permission.objects.using(using).filter(codename__in=stale).delete()   # en cascada, sus RolePermission
            deleted = len(stale)
    return SyncResult(created, updated, deleted)
