"""Modelo de usuario personalizado de Workspace."""
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

BIO_MAX_LENGTH = 280


def avatar_path(instance, filename: str) -> str:
    # ``filename`` llega como "<user_id>.webp" desde services.profile.
    return f"avatars/{filename}"


class Gender(models.TextChoices):
    MALE = "male", "Hombre"
    FEMALE = "female", "Mujer"


class MaritalStatus(models.TextChoices):
    SINGLE = "single", "Soltero(a)"
    IN_RELATIONSHIP = "in_relationship", "En una relación"
    MARRIED = "married", "Casado(a)"
    COMMON_LAW = "common_law", "Unión libre"
    DIVORCED = "divorced", "Divorciado(a)"
    WIDOWED = "widowed", "Viudo(a)"
    COMPLICATED = "complicated", "Es complicado"


class User(AbstractUser):
    """Usuario de Workspace.

    Extiende AbstractUser para conservar la autenticación nativa de Django.
    Los roles (negocio) se asignan mediante ``UserRole`` y no deben confundirse
    con departamentos ni cargos laborales.

    Perfil:
    - Lo administra RRHH/TI (admin): ``job_title``, ``department``, ``manager``, ``birth_date``, ``gender``, ``marital_status``. No hay sede: todo el personal está en Querétaro.
    - ``department`` (tabla ``org.Department``) y ``manager`` (jefe directo, arma el organigrama) se
      mudarán a la tabla de empleados cuando se defina (ver docs/backlog.md).
    - Lo edita cada persona: ``avatar`` y ``bio``. La portada del perfil es estática (igual para todos).
    La foto se guarda como ``avatars/<id>.webp`` y se entrega por una vista autorizada;
    ``profile_updated_at`` sirve para invalidar la caché del navegador.
    """

    email = models.EmailField("correo electrónico", unique=True)
    job_title = models.CharField("cargo", max_length=120, blank=True)
    department = models.ForeignKey(
        "org.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="members",
        verbose_name="departamento",
    )
    manager = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="direct_reports",
        verbose_name="jefe directo",
    )
    bio = models.CharField("presentación", max_length=BIO_MAX_LENGTH, blank=True)
    birth_date = models.DateField(
        "fecha de nacimiento", null=True, blank=True,
        help_text="Para el widget de cumpleaños. Solo se muestran el día y el mes; el año (la edad) nunca se publica.",
    )
    gender = models.CharField("género", max_length=10, choices=Gender.choices, null=True, blank=True)
    marital_status = models.CharField(
        "estado civil", max_length=20, choices=MaritalStatus.choices, null=True, blank=True,
    )
    avatar = models.ImageField("foto de perfil", upload_to=avatar_path, blank=True, max_length=255)
    profile_updated_at = models.DateTimeField("perfil actualizado el", null=True, blank=True)

    roles = models.ManyToManyField(
        "accounts.Role",
        through="accounts.UserRole",
        through_fields=("user", "role"),
        related_name="users",
        blank=True,
        verbose_name="roles",
    )

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["username"]

    def __str__(self) -> str:
        return self.get_full_name() or self.username

    def clean(self):
        """El jefe directo no puede ser la misma persona ni alguien que (directa o indirectamente) le reporta."""
        super().clean()
        seen = {self.pk}
        manager = self.manager
        while manager is not None:
            if manager.pk in seen:
                raise ValidationError({"manager": "Esa persona le reporta a este usuario: se formaría un ciclo."})
            seen.add(manager.pk)
            manager = manager.manager

    @property
    def display_name(self) -> str:
        return self.get_full_name() or self.username

    @property
    def age(self) -> int | None:
        """Años cumplidos hoy (zona del servidor); ``None`` sin fecha de nacimiento. Uso interno: no se publica."""
        if self.birth_date is None:
            return None
        today = timezone.localdate()
        had_birthday = (today.month, today.day) >= (self.birth_date.month, self.birth_date.day)
        return today.year - self.birth_date.year - (0 if had_birthday else 1)
