from pathlib import Path

from django.core.management.base import BaseCommand

from apps.accounts.services.role_catalog import DEFAULT_ROLES_JSON, read_roles_json, sync_roles


class Command(BaseCommand):
    help = "Crea los roles básicos de apps/accounts/data/roles.json que no existan."

    def add_arguments(self, parser):
        parser.add_argument("--file", type=Path, default=DEFAULT_ROLES_JSON, help="Ruta al JSON de roles.")
        parser.add_argument(
            "--update", action="store_true",
            help="También deja los roles que ya existen exactamente como en el JSON (descripción, por defecto y permisos).",
        )

    def handle(self, *args, **options):
        result = sync_roles(read_roles_json(options["file"]), update=options["update"])
        self.stdout.write(self.style.SUCCESS(f"Roles: {result.created} creados, {result.updated} actualizados."))
