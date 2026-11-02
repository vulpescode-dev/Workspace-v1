"""Envía el correo de prueba con la plantilla de Workspace (emails/test) para revisar el diseño y el envío.

    python manage.py runscript send_test_email --script-args tu@correo.com

Sin servidor SMTP configurado se imprime en la consola. Para probar solo la conexión SMTP, Django
trae su propio comando: python manage.py sendtestemail tu@correo.com
"""
from apps.core.mail import send_email


def run(*args):
    if not args:
        raise SystemExit("Uso: python manage.py runscript send_test_email --script-args tu@correo.com")
    sent = send_email(to=list(args), subject="Prueba de correo de Workspace", template="test", context={"name": ""})
    print(f"Listo: {sent} correo(s) enviado(s).")
