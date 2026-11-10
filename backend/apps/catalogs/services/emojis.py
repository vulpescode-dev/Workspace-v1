"""Carga del catálogo de emojis desde el JSON del repositorio."""
import json
from dataclasses import dataclass
from pathlib import Path

from django.db import transaction

DEFAULT_EMOJIS_JSON = Path(__file__).resolve().parent.parent / "data" / "emojis.json"
FIELDS = ("codepoint", "char", "label", "position")


@dataclass(frozen=True)
class LoadResult:
    created: int
    updated: int
    deactivated: int


def read_emojis_json(path: Path = DEFAULT_EMOJIS_JSON) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    emojis = data["emojis"]
    codes = [item["code"] for item in emojis]
    if len(codes) != len(set(codes)):
        raise ValueError("El catálogo de emojis tiene códigos repetidos.")
    return emojis


@transaction.atomic
def load_emojis(items: list[dict], emoji_model=None) -> LoadResult:
    """Crea/actualiza los emojis del JSON. Los que ya no están se desactivan, nunca se borran.

    ``emoji_model`` permite usarla desde una migración con el modelo histórico.
    """
    if emoji_model is None:
        from apps.catalogs.models import Emoji as emoji_model

    existing = {e.code: e for e in emoji_model.objects.all()}
    created = updated = 0
    for item in items:
        values = {field: item[field] for field in FIELDS}
        values["is_active"] = item.get("active", True)
        emoji = existing.pop(item["code"], None)
        if emoji is None:
            emoji_model.objects.create(code=item["code"], **values)
            created += 1
        elif any(getattr(emoji, k) != v for k, v in values.items()):
            for key, value in values.items():
                setattr(emoji, key, value)
            emoji.save()
            updated += 1
    deactivated = emoji_model.objects.filter(pk__in=[e.pk for e in existing.values() if e.is_active]).update(is_active=False)
    return LoadResult(created, updated, deactivated)
