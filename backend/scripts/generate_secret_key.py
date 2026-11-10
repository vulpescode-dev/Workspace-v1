"""Genera una DJANGO_SECRET_KEY aleatoria y la escribe en ``backend/.env``.

    python manage.py runscript scripts.generate_secret_key
    python manage.py runscript scripts.generate_secret_key --script-args --force   # rotarla

Va después de ``cp .env.example .env`` y antes de ``migrate``. Solo reemplaza la clave si está vacía o
sigue siendo la de ejemplo; para cambiar una clave real usa ``--force`` (cierra todas las sesiones:
los JWT y enlaces firmados con la clave anterior dejan de valer).

También corre sin Django: ``python scripts/generate_secret_key.py [--force]``.
"""
import re
import secrets
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
PLACEHOLDERS = {"", "cambia-esto-por-una-clave-larga-y-aleatoria"}
LINE = re.compile(r"^DJANGO_SECRET_KEY=(.*)$", re.MULTILINE)


def generate(force: bool = False) -> str:
    if not ENV_FILE.exists():
        raise SystemExit(f"No existe {ENV_FILE}. Primero: cp .env.example .env")

    with ENV_FILE.open(encoding="utf-8", newline="") as fh:
        text = fh.read()

    match = LINE.search(text)
    current = match.group(1).strip().strip("'\"") if match else ""
    if current not in PLACEHOLDERS and not force:
        return "DJANGO_SECRET_KEY ya tiene una clave propia; no se tocó (usa --force para rotarla)."

    # token_urlsafe solo usa letras, números, «-» y «_»: nada que .env interprete como comentario o variable.
    new_line = f"DJANGO_SECRET_KEY={secrets.token_urlsafe(50)}"
    if match:
        text = text[: match.start()] + new_line + text[match.end():]
    else:
        text = text.rstrip("\r\n") + "\n" + new_line + "\n"

    with ENV_FILE.open("w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    return f"DJANGO_SECRET_KEY nueva escrita en {ENV_FILE}."


def run(*args):
    print(generate(force="--force" in args))


if __name__ == "__main__":
    import sys

    run(*sys.argv[1:])
