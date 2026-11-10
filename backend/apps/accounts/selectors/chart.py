"""Organigrama: árbol de personas por jefe directo (``User.manager``).

Se arma en memoria con una sola consulta (personas activas; ~500 hoy). Raíces: quien no tiene
jefe activo y sí tiene a alguien a su cargo. Quien no tiene jefe ni personas a cargo todavía no
está en el organigrama: solo se cuenta (``unassigned_count``) para que RRHH lo complete.
Con ``depth`` se corta la profundidad; cada nodo trae ``reports_count`` para pedir más
(``?root=<id>``) sin cargar todo el árbol.
"""
from dataclasses import dataclass, field

from apps.accounts.models import User

DEFAULT_DEPTH = 3
MAX_DEPTH = 10


@dataclass
class ChartNode:
    user: User
    reports_count: int
    children: list["ChartNode"] = field(default_factory=list)


@dataclass
class Chart:
    roots: list[ChartNode]
    unassigned_count: int


def _people():
    return list(
        User.objects.filter(is_active=True)
        .select_related("department")
        .only(
            "id", "first_name", "last_name", "username", "job_title", "manager_id", "avatar", "profile_updated_at",
            "department__id", "department__name",
        )
        .order_by("first_name", "last_name", "username", "id")
    )


def org_chart(viewer, *, root_id: int | None = None, depth: int = DEFAULT_DEPTH) -> Chart | None:
    """Árbol completo (``root_id`` vacío) o desde una persona. ``None`` si ``root_id`` no es una persona activa."""
    if not getattr(viewer, "is_authenticated", False) or not viewer.is_active:
        return Chart([], 0)
    people = _people()
    by_id = {person.pk: person for person in people}
    reports: dict[int, list[User]] = {}
    for person in people:
        if person.manager_id in by_id and person.manager_id != person.pk:
            reports.setdefault(person.manager_id, []).append(person)

    def build(person: User, level: int, path: frozenset) -> ChartNode:
        direct = reports.get(person.pk, [])
        node = ChartNode(person, len(direct))
        if level < depth:
            # ``path`` evita vueltas infinitas si en la base hubiera un ciclo (el admin lo impide).
            node.children = [build(child, level + 1, path | {child.pk}) for child in direct if child.pk not in path]
        return node

    if root_id is not None:
        root = by_id.get(root_id)
        if root is None:
            return None
        return Chart([build(root, 1, frozenset({root.pk}))], 0)

    without_manager = [p for p in people if p.manager_id not in by_id or p.manager_id == p.pk]
    roots = [p for p in without_manager if p.pk in reports]
    return Chart(
        [build(root, 1, frozenset({root.pk})) for root in roots],
        unassigned_count=len(without_manager) - len(roots),
    )
