"""Crea o reutiliza los bots de relleno y sus seguimientos (solo desarrollo).

    python manage.py runscript scripts.bots.create_bots

Desde otro script:

    from scripts.bots.create_bots import get_bots
    bots = get_bots()          # en el orden de ``PERSONAS``

Cada bot se busca por su ``username``: si ya existe se reutiliza tal cual (sus publicaciones,
seguidores y reacciones siguen siendo suyos); si no, se crea con contraseña «1234», cargo, área,
presentación, foto y fecha de nacimiento. Así, correr el script varias veces nunca duplica bots.

Seguimientos (``sync_follows``), con el servicio ``follow`` de la app:

- Entre bots: exactamente los de ``follows`` en ``personas.py`` (si un bot sigue a otro bot que
  no está en su lista, se deja de seguir). No todos se siguen ni todo es recíproco.
- Administración: quien tenga ``follows_admin`` sigue a todas las cuentas activas con
  ``is_superuser`` (sin usuario, id ni correo fijos).
- Personas reales: hasta ``follows_people`` cuentas activas que no son bots. Solo se agregan
  seguimientos; nunca se toca lo que siguen o dejan de seguir las personas reales.
"""
import os
import random
from datetime import date, timedelta

from django.conf import settings
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services.profile import set_profile_image, update_bio
from apps.accounts.models import Department
from apps.social.models import Follow
from apps.social.services.follows import follow, unfollow

from scripts.bots.personas import PERSONAS
from scripts.fake_media import avatar

BOT_PASSWORD = "1234"
BOT_PREFIX = "bot."
ALLOW_ENV = "WORKSPACE_ALLOW_BOTS"


def ensure_dev() -> None:
    """Los bots tienen contraseña débil: nunca deben existir en producción.

    Corre con ``DEBUG=True`` (settings de desarrollo). Con ``DEBUG=False`` solo si además se
    pone ``WORKSPACE_ALLOW_BOTS=1`` a propósito (p. ej. un servidor de pruebas).
    """
    if not settings.DEBUG and os.getenv(ALLOW_ENV) != "1":
        raise SystemExit(f"Estos scripts son solo para desarrollo (DEBUG=True o {ALLOW_ENV}=1).")


def _birth_date(data) -> date:
    """Cumpleaños a ``birthday_in`` días de hoy (para que el widget de cumpleaños tenga qué mostrar)."""
    day = timezone.localdate() + timedelta(days=data["birthday_in"])
    if day.month == 2 and day.day == 29:
        day -= timedelta(days=1)
    return day.replace(year=data["birth_year"])


def _department(name: str) -> Department:
    """Departamento del bot por nombre (sin distinguir mayúsculas); se crea si no existe."""
    return Department.objects.filter(name__iexact=name).first() or Department.objects.create(name=name)


def get_bots(verbose: bool = True) -> list[User]:
    """Los bots, en el orden de ``PERSONAS``; crea los que no existan."""
    ensure_dev()
    bots = []
    for data in PERSONAS:
        user = User.objects.filter(username=data["username"]).first()
        if user is None:
            user = User(
                username=data["username"], email=f'{data["username"]}@workspace.test',
                first_name=data["first_name"], last_name=data["last_name"],
                job_title=data["job_title"], department=_department(data["department"]), birth_date=_birth_date(data),
            )
            user.set_password(BOT_PASSWORD)
            user.save()
            update_bio(user=user, bio=data["bio"])
            initials = data["first_name"][0] + data["last_name"][0]
            set_profile_image(user=user, field="avatar", upload=avatar(initials, data["color"]))
            if verbose:
                print(f"  + creado  {user.username} ({user.display_name})")
        else:
            if user.birth_date is None:   # bots creados antes de existir el campo: solo se completa lo que falta
                user.birth_date = _birth_date(data)
                user.save(update_fields=["birth_date"])
            if verbose:
                print(f"  = existe  {user.username} ({user.display_name})")
        bots.append(user)
    return bots


def get_admins():
    """Quien administra: cuentas activas con ``is_superuser`` (como ``/admin/`` y los permisos)."""
    return User.objects.filter(is_active=True, is_superuser=True).exclude(username__startswith=BOT_PREFIX)


def sync_follows(bots: list[User], verbose: bool = True) -> dict:
    """Deja los seguimientos de los bots como dicen sus personas. Idempotente."""
    by_username = {bot.username: bot for bot in bots}
    bot_ids = set(by_username[name].pk for name in by_username)
    admins = list(get_admins())
    people = list(
        User.objects.filter(is_active=True).exclude(username__startswith=BOT_PREFIX)
        .exclude(pk__in=[admin.pk for admin in admins]).order_by("pk")
    )
    totals = {"new": 0, "removed": 0}

    for data, bot in zip(PERSONAS, bots):
        current = set(Follow.objects.filter(follower=bot).values_list("following_id", flat=True))
        wanted = {by_username[name] for name in data["follows"]}
        if data["follows_admin"]:
            wanted.update(admins)

        # Personas reales: se completan hasta el máximo; la elección es estable por bot.
        already = len(current - bot_ids - {admin.pk for admin in admins})
        missing = data["follows_people"] - already
        if missing > 0:
            candidates = [person for person in people if person.pk not in current]
            random.Random(bot.username).shuffle(candidates)
            wanted.update(candidates[:missing])

        for target in wanted:
            if target.pk not in current:
                follow(user=bot, target=target)
                totals["new"] += 1
        # Entre bots manda la lista: se quitan los que sobran (p. ej. del antiguo «todos con todos»).
        for target in bots:
            if target.pk in current and target not in wanted:
                unfollow(user=bot, target=target)
                totals["removed"] += 1

        if verbose:
            following = Follow.objects.filter(follower=bot).select_related("following").order_by("following__username")
            print(f"  {bot.username:<10} sigue a: {', '.join(f.following.username for f in following) or '—'}")
    return totals


def run(*args):
    print("Bots:")
    bots = get_bots()
    print("\nSeguimientos:")
    totals = sync_follows(bots)
    if not get_admins().exists():
        print("  (no hay cuentas con is_superuser: ningún bot sigue a administración)")
    print(f"\n{totals['new']} seguimientos nuevos, {totals['removed']} quitados entre bots.")
    print(f"Contraseña de todos: «{BOT_PASSWORD}»")
