from pathlib import Path

from django.core.management.base import BaseCommand

from apps.catalogs.services.emojis import DEFAULT_EMOJIS_JSON, load_emojis, read_emojis_json


class Command(BaseCommand):
    help = "Carga/actualiza los catálogos compartidos desde sus JSON (hoy: emojis de reacciones)."

    def add_arguments(self, parser):
        parser.add_argument("--emojis", type=Path, default=DEFAULT_EMOJIS_JSON, help="Ruta al JSON de emojis.")

    def handle(self, *args, **options):
        result = load_emojis(read_emojis_json(options["emojis"]))
        self.stdout.write(self.style.SUCCESS(
            f"Emojis: {result.created} creados, {result.updated} actualizados, {result.deactivated} desactivados."
        ))
