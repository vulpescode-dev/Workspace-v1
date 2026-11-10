"""Notificaciones (en la app se muestran como «Avisos»), generales para todo Workspace.

A propósito simples: cada aviso trae solo lo necesario para mostrarse (título, descripción, ícono,
color, fecha y a dónde lleva). Quien lo crea —social, documentos, formularios, sistema, RRHH—
decide esos valores; no dependen de ninguna otra app.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    class Color(models.TextChoices):
        PRIMARY = "primary", "Azul (marca)"
        SECONDARY = "secondary", "Amarillo (marca)"
        SUCCESS = "success", "Verde"
        DANGER = "danger", "Rojo (urgente)"
        WARNING = "warning", "Ámbar (importante)"
        INFO = "info", "Celeste (informativo)"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications", verbose_name="para"
    )
    title = models.CharField("título", max_length=160)
    body = models.CharField("descripción", max_length=300, blank=True)
    icon = models.CharField("ícono", max_length=40, default="bx-bell", help_text="Clase de Boxicons, p. ej. bx-wrench.")
    color = models.CharField("color", max_length=12, choices=Color.choices, default=Color.PRIMARY)
    url = models.CharField("enlace", max_length=300, blank=True, help_text="Ruta interna a la que lleva al tocarla.")
    # Identifica el evento que la originó (p. ej. «social.post_reaction:12:7»): con la misma clave se
    # actualiza en vez de duplicarse, y al deshacer la acción se retira. Vacía = aviso suelto.
    key = models.CharField("clave del evento", max_length=120, blank=True, db_index=True)
    created_at = models.DateTimeField("fecha", default=timezone.now, db_index=True)
    read_at = models.DateTimeField("leída el", null=True, blank=True)

    class Meta:
        verbose_name = "notificación"
        verbose_name_plural = "notificaciones"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["recipient", "-created_at"], name="notif_recipient_created_idx"),
            models.Index(fields=["recipient", "key"], name="notif_recipient_key_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.recipient}: {self.title}"


class PushSubscription(models.Model):
    """Un dispositivo (navegador o PWA instalada) donde la persona aceptó recibir notificaciones push.

    Guarda lo que entrega el navegador al suscribirse con la Push API
    (``PushManager.subscribe()`` → ``subscription.toJSON()``): ``endpoint`` (URL única del
    servicio push del navegador) y las llaves ``p256dh`` y ``auth`` para cifrar el mensaje.
    Una persona puede tener varias (celular, laptop…); el ``endpoint`` es único: si el mismo
    navegador vuelve a suscribirse, se actualiza el registro en lugar de duplicarlo.

    Si el servicio push responde 404/410 al enviar, la suscripción ya no sirve y se borra.
    No es la sesión de Django: cerrar sesión no la borra por sí solo (decidir en el backlog).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_subscriptions", verbose_name="usuario"
    )
    endpoint = models.URLField("endpoint", max_length=500, unique=True)
    p256dh = models.CharField("llave p256dh", max_length=200)
    auth = models.CharField("llave auth", max_length=100)
    user_agent = models.CharField("navegador / dispositivo", max_length=300, blank=True)
    created_at = models.DateTimeField("suscrita el", auto_now_add=True)
    last_used_at = models.DateTimeField(
        "último envío", null=True, blank=True, help_text="Último push enviado con éxito a este dispositivo."
    )

    class Meta:
        verbose_name = "suscripción push"
        verbose_name_plural = "suscripciones push"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.user} · {self.user_agent[:40] or self.endpoint[:40]}"
