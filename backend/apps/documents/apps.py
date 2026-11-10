from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    """Documentos: biblioteca interna con categorías, privacidad por documento e historial de versiones.

    Suben documentos quienes tengan ``documents.documents.create``; cada dueño administra los suyos y
    ``documents.documents.manage`` administra todos. Etapa actual: modelos, servicios y API; la pantalla
    está pendiente (ver docs/backlog.md).
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.documents"
    verbose_name = "Documentos"
