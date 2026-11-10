from pathlib import Path

from django.core.management.base import BaseCommand

from apps.accounts.services.permission_catalog import DEFAULT_PERMISSIONS_JSON, read_permissions_json, sync_permissions


class Command(BaseCommand):
    help = "Carga/actualiza los permisos de negocio desde su catálogo JSON (apps/accounts/data/permissions.json)."

    def add_arguments(self, parser):
        parser.add_argument("--file", type=Path, default=DEFAULT_PERMISSIONS_JSON, help="Ruta al JSON de permisos.")
        parser.add_argument(
            "--prune", action="store_true",
            help="Borra los permisos que ya no estén en el catálogo (y su asignación a roles).",
        )

    def handle(self, *args, **options):
        result = sync_permissions(read_permissions_json(options["file"]), prune=options["prune"])
        self.stdout.write(self.style.SUCCESS(
            f"Permisos: {result.created} creados, {result.updated} actualizados, {result.deleted} borrados."
        ))
