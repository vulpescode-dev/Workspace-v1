"""Consultas de departamentos. Cualquier persona autenticada y activa ve los departamentos activos."""
from django.db.models import Count, Q

from apps.accounts.models import Department


def active_departments(user):
    """Departamentos activos con ``members_count`` (personas activas), por nombre."""
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return Department.objects.none()
    return (
        Department.objects.filter(is_active=True)
        .select_related("head")
        .annotate(members_count=Count("members", filter=Q(members__is_active=True)))
        .order_by("name")   # con annotate, Django no aplica Meta.ordering
    )
