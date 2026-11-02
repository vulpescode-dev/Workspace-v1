from django.apps import AppConfig


class HelpdeskConfig(AppConfig):
    """Mesa de ayuda: tickets (incidencias y solicitudes) que atiende cada departamento.

    La persona elige una categoría («Acceso a ERP», «Limpieza de piso») y el ticket llega al
    departamento de esa categoría. Lo atienden sus agentes: integrantes del departamento con el
    permiso de negocio ``helpdesk.tickets.attend`` y el responsable del departamento.
    Etapa actual: modelos, servicios y API; la pantalla está pendiente (ver docs/backlog.md).
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.helpdesk"
    verbose_name = "Mesa de ayuda"
