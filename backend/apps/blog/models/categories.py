from django.db import models


class ArticleCategory(models.Model):
    """Categoría de artículos (los chips para filtrar: «Aniversarios», «RRHH», «Celebración»…).

    Las define la empresa desde el admin. Desactivada: deja de aparecer en los filtros, pero sus
    artículos la conservan.
    """

    name = models.CharField("nombre", max_length=60, unique=True)
    slug = models.SlugField("slug", max_length=70, unique=True)
    position = models.PositiveSmallIntegerField("orden", default=0)
    is_active = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "categoría de artículo"
        verbose_name_plural = "categorías de artículos"
        ordering = ["position", "name"]

    def __str__(self) -> str:
        return self.name
