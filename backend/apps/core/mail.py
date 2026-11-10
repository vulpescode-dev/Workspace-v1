"""Envío de correos del proyecto (remitente no-reply@, ver «Correo» en config/settings/base.py).

Un solo punto de salida para todas las apps:

    from apps.core.mail import send_email
    send_email(to=user.email, subject="Te invitaron a un formulario", template="forms/invitation",
               context={"form": form, "url": absolute_url(form_url)})

- Cada correo lleva versión HTML y de texto: ``templates/emails/<template>.html`` y ``.txt``. Las
  plantillas HTML extienden ``emails/base.html`` (marca, pie «no respondas a este correo»).
- Se envía UN correo por destinatario (misma conexión): nadie ve las direcciones de los demás.
- Los errores de envío se propagan (``fail_silently=False``): quien llama decide si reintenta o avisa.
  Cuando haya envíos masivos o lentos, conviene moverlos a segundo plano (pendiente).
- Mientras la cuenta no-reply@ no exista, el backend de consola imprime los correos en el servidor.
"""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string


def absolute_url(path: str) -> str:
    """URL completa para usar dentro de un correo (los correos no entienden rutas relativas)."""
    if path.startswith(("http://", "https://")):
        return path
    return settings.SITE_URL + ("" if path.startswith("/") else "/") + path


def send_email(*, to, subject: str, template: str, context: dict | None = None, reply_to=None) -> int:
    """Envía ``emails/<template>`` a uno o varios destinatarios. Devuelve cuántos correos salieron."""
    recipients = [to] if isinstance(to, str) else [address for address in to if address]
    if not recipients:
        return 0
    context = {"site_name": settings.PROJECT_NAME, "site_url": settings.SITE_URL, "subject": subject, **(context or {})}
    text = render_to_string(f"emails/{template}.txt", context)
    html = render_to_string(f"emails/{template}.html", context)

    messages = []
    for address in recipients:
        message = EmailMultiAlternatives(
            subject=subject, body=text, from_email=settings.DEFAULT_FROM_EMAIL, to=[address],
            reply_to=[reply_to] if isinstance(reply_to, str) else reply_to,
        )
        message.attach_alternative(html, "text/html")
        messages.append(message)
    with get_connection(fail_silently=False) as connection:
        return connection.send_messages(messages) or 0
