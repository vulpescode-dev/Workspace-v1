"""Scripts del proyecto (django-extensions).

Cada archivo ``scripts/<nombre>.py`` define ``def run(*args):`` y se ejecuta con todo Django
cargado (modelos, settings). En subcarpetas se usa la ruta completa con puntos:

    python manage.py runscript <nombre>
    python manage.py runscript <nombre> --script-args valor1 valor2
    python manage.py runscript scripts.<carpeta>.<nombre>

Scripts disponibles (solo desarrollo, se niegan a correr con DEBUG=False salvo WORKSPACE_ALLOW_BOTS=1):

- ``scripts.bots.create_bots``  — crea o reutiliza los 8 bots (contraseña «1234») y sus
                                  seguimientos. Base para los demás scripts:
                                  ``from scripts.bots.create_bots import get_bots``.
- ``scripts.bots.create_posts`` — publicaciones con la voz de cada bot (texto, 1–10 imágenes,
                                  solo seguidores) con reacciones, comentarios y respuestas.
                                  Cada corrida agrega más (24 o ``--script-args N``).

Las personalidades están en ``scripts/bots/personas.py``.

- ``make_icons``                — regenera los íconos de la app (PWA, iPhone y favicon) desde el logo
                                  del encabezado. Solo si cambia el logo o el color.
- ``send_test_email``           — envía el correo de prueba con la plantilla de Workspace
                                  (``--script-args tu@correo.com``). Sin SMTP, sale en la consola.

``fake_media`` no es un script: genera imágenes WebP de relleno para los demás.
"""
