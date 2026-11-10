"""Editar el propio perfil: presentación y foto (la portada es estática, no se edita).

Las imágenes llegan ya en WebP desde el navegador (``Workspace.procesarAWebP``) y aquí se
validan con ``apps.core.uploads`` (solo WebP real). Se guardan como ``<user_id>.webp``,
reemplazando la anterior.
"""
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.models.auth import BIO_MAX_LENGTH
from apps.core.uploads import KIND_IMAGE, check_media_upload

IMAGE_FIELDS = {"avatar"}


def _touch(user: User, *fields: str) -> None:
    user.profile_updated_at = timezone.now()
    user.save(update_fields=[*fields, "profile_updated_at"])


def update_bio(*, user: User, bio: str) -> User:
    bio = " ".join((bio or "").split())   # una sola línea, sin espacios repetidos
    if len(bio) > BIO_MAX_LENGTH:
        raise ValidationError({"bio": f"Máximo {BIO_MAX_LENGTH} caracteres."})
    user.bio = bio
    _touch(user, "bio")
    return user


def set_profile_image(*, user: User, field: str, upload) -> User:
    assert field in IMAGE_FIELDS
    info = check_media_upload(upload)
    if info.kind != KIND_IMAGE:
        raise ValidationError({"file": "Debe ser una imagen."})
    current = getattr(user, field)
    if current:
        current.delete(save=False)            # mismo nombre <id>.webp: se borra la anterior primero
    getattr(user, field).save(f"{user.pk}.webp", upload, save=False)
    _touch(user, field)
    return user


def remove_profile_image(*, user: User, field: str) -> User:
    assert field in IMAGE_FIELDS
    current = getattr(user, field)
    if current:
        current.delete(save=False)
    setattr(user, field, "")
    _touch(user, field)
    return user
