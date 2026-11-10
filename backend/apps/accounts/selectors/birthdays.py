"""Cumpleaños próximos (widget de la portada).

Solo día y mes: el año de nacimiento nunca sale del servidor. Quien nació un 29 de febrero
celebra el 28 en los años que no son bisiestos. «Hoy» es la fecha de la sede (``TIME_ZONE``).
"""
import calendar
from dataclasses import dataclass
from datetime import date

from django.utils import timezone

from apps.accounts.models import User


@dataclass
class Birthday:
    user: User
    next_date: date
    days_until: int


def _occurrence(birth: date, year: int) -> date:
    day = birth.day
    if birth.month == 2 and day == 29 and not calendar.isleap(year):
        day = 28
    return date(year, birth.month, day)


def upcoming_birthdays(viewer, days: int = 30, limit: int = 6) -> list[Birthday]:
    """Personas activas que cumplen años hoy o en los próximos ``days`` días, la más cercana primero."""
    if not getattr(viewer, "is_authenticated", False) or not viewer.is_active:
        return []
    today = timezone.localdate()
    found = []
    # Se calcula en Python: la plantilla de personal es chica (cientos). Con miles, mover a SQL.
    for user in User.objects.filter(is_active=True, birth_date__isnull=False).only(
        "id", "first_name", "last_name", "username", "job_title", "birth_date", "avatar", "profile_updated_at"
    ):
        next_date = _occurrence(user.birth_date, today.year)
        if next_date < today:
            next_date = _occurrence(user.birth_date, today.year + 1)
        days_until = (next_date - today).days
        if days_until <= days:
            found.append(Birthday(user, next_date, days_until))
    found.sort(key=lambda b: (b.days_until, b.user.first_name, b.user.pk))
    return found[:limit]
