"""Lectura de seguidores / seguidos."""
from django.db.models import Case, Count, IntegerField, Q, Value, When

from apps.accounts.models import User
from apps.social.models import Follow


def follow_stats(target: User, viewer) -> dict:
    """Contadores y relación de ``viewer`` con ``target`` (para el perfil)."""
    return {
        "followers_count": Follow.objects.filter(following=target, follower__is_active=True).count(),
        "following_count": Follow.objects.filter(follower=target, following__is_active=True).count(),
        "is_following": Follow.objects.filter(follower=viewer, following=target).exists(),
        "follows_me": Follow.objects.filter(follower=target, following=viewer).exists(),
    }


def followers_of(target: User):
    """Personas activas que siguen a ``target``, más recientes primero."""
    return User.objects.filter(is_active=True, following_set__following=target).order_by("-following_set__created_at", "-id")


def following_of(target: User):
    """Personas activas a las que sigue ``target``, más recientes primero."""
    return User.objects.filter(is_active=True, followers_set__follower=target).order_by("-followers_set__created_at", "-id")


def followed_ids(viewer, user_ids) -> set[int]:
    """De ``user_ids``, a quiénes sigue ``viewer`` (para los botones de las listas, en una consulta)."""
    return set(Follow.objects.filter(follower=viewer, following_id__in=list(user_ids)).values_list("following_id", flat=True))


def follow_suggestions(viewer, limit: int = 5):
    """Personas activas que ``viewer`` aún no sigue (widget «Personas que quizás conozcas»).

    Orden: primero su mismo departamento, luego quienes tienen más seguidores y al final las cuentas más nuevas.
    """
    if not getattr(viewer, "is_authenticated", False) or not viewer.is_active:
        return User.objects.none()
    same_area = Value(0)
    if viewer.department_id:
        same_area = Case(When(department_id=viewer.department_id, then=Value(1)), default=Value(0), output_field=IntegerField())
    return (
        User.objects.filter(is_active=True)
        .exclude(pk=viewer.pk)
        .exclude(followers_set__follower=viewer)
        .annotate(same_area=same_area, followers=Count("followers_set", filter=Q(followers_set__follower__is_active=True)))
        .order_by("-same_area", "-followers", "-date_joined", "-id")[:limit]
    )
