"""Lectura del archivo ``backend/.env``: un solo lugar para cargarlo y convertir sus valores.

Se importa antes que Django (``manage.py``, ``wsgi.py``, ``asgi.py``) porque ``DJANGO_ENV`` decide qué
archivo de ajustes se usa. Lo que cambie entre equipos o servidores va en ``.env``, no en los ``.py``.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_MODULES = {"development", "production"}


def load_env() -> None:
    """Carga ``backend/.env`` (sin pisar variables que ya existan en el sistema) y elige los ajustes."""
    load_dotenv(BASE_DIR / ".env")
    environment = env_str("DJANGO_ENV", "development")
    if environment not in SETTINGS_MODULES:
        raise RuntimeError(f"DJANGO_ENV debe ser uno de {sorted(SETTINGS_MODULES)}, no «{environment}».")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"config.settings.{environment}")


def env_str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def env_bool(name: str, default: bool = False) -> bool:
    return env_str(name, str(default)).lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    return int(env_str(name, str(default)))


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]
