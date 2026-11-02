from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Notificaciones personales dentro de la app («Ana reaccionó a tu publicación»).

    API completa (listar, leídas, contador, eliminar) y registro de dispositivos push. Todavía NO
    se generan desde las demás apps ni se envían los push; ver docs/backlog.md. No son los Avisos oficiales.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    verbose_name = "Notificaciones"
