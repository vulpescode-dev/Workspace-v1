"""Comprobaciones de salud de la app (las usa ``/api/health/``).

Cada comprobación devuelve ``(ok, detalle)``. El detalle (tiempos, errores, pendientes) solo se
muestra a personal (``is_staff``): a cualquier otro solo se le dice qué está bien y qué no, para
no exponer información interna a un monitor externo o a quien no tenga sesión.
"""
import os
import platform
import time

import django
from django.apps import apps
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.executor import MigrationExecutor


def check_database() -> tuple[bool, dict]:
    """La base responde a una consulta mínima."""
    start = time.perf_counter()
    try:
        with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:   # cualquier falla de conexión cuenta como caída
        return False, {"error": f"{type(exc).__name__}: {exc}"}
    return True, {"engine": connections[DEFAULT_DB_ALIAS].vendor, "ms": round((time.perf_counter() - start) * 1000, 1)}


def check_migrations() -> tuple[bool, dict]:
    """No hay migraciones sin aplicar (código nuevo con la base vieja rompe pantallas)."""
    try:
        executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    except Exception as exc:
        return False, {"error": f"{type(exc).__name__}: {exc}"}
    pending = [f"{migration.app_label}.{migration.name}" for migration, _ in plan]
    return not pending, {"pending": pending}


def check_storage() -> tuple[bool, dict]:
    """La carpeta de archivos subidos (MEDIA_ROOT) existe y se puede escribir."""
    path = str(settings.MEDIA_ROOT)
    ok = os.path.isdir(path) and os.access(path, os.W_OK)
    return ok, {} if ok else {"error": f"MEDIA_ROOT no existe o no se puede escribir: {path}"}


def check_catalogs() -> tuple[bool, dict]:
    """Los datos base están cargados (sin emojis no se puede reaccionar)."""
    from apps.catalogs.models import Emoji
    try:
        count = Emoji.objects.filter(is_active=True).count()
    except Exception as exc:
        return False, {"error": f"{type(exc).__name__}: {exc}"}
    if not count:
        return False, {"error": "No hay emojis activos: corre «python manage.py load_catalogs»."}
    return True, {"emojis": count}


CHECKS = {
    "database": check_database,
    "migrations": check_migrations,
    "storage": check_storage,
    "catalogs": check_catalogs,
}


def run_checks(*, detailed: bool = False) -> dict:
    """Corre todas las comprobaciones. Si la base no responde, las que dependen de ella no se intentan."""
    results, details = {}, {}
    for name, check in CHECKS.items():
        if name in ("migrations", "catalogs") and results.get("database") == "error":
            results[name], details[name] = "error", {"error": "Sin base de datos."}
            continue
        ok, detail = check()
        results[name] = "ok" if ok else "error"
        details[name] = detail

    report = {"status": "ok" if all(v == "ok" for v in results.values()) else "error", "checks": results}
    if detailed:
        report["details"] = details
        report["apps"] = sorted(config.name for config in apps.get_app_configs() if config.name.startswith("apps."))
        report["environment"] = {
            "debug": settings.DEBUG,
            "settings": os.environ.get("DJANGO_SETTINGS_MODULE", ""),
            "django": django.get_version(),
            "python": platform.python_version(),
        }
    return report
