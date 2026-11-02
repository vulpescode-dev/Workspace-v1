from django.apps import AppConfig


class OrgConfig(AppConfig):
    """Estructura de la empresa: departamentos (con subáreas y responsable) y organigrama.

    El departamento de cada persona y su jefe directo viven en ``accounts.User`` mientras se define
    la tabla de empleados (ver docs/backlog.md). Los departamentos los administra RRHH/TI en el admin.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.org"
    verbose_name = "Organización"
