from django.apps import AppConfig


class MarketplaceConfig(AppConfig):
    """Compra-venta entre compañeros: cada persona publica artículos con fotos y los marca como vendidos.

    Etapa actual: modelos, servicios y API. Sin pantallas, reacciones, preguntas ni contacto
    privado todavía (ver docs/backlog.md).
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.marketplace"
    verbose_name = "Marketplace"
