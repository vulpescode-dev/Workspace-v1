"""Correo (apps/core/mail.py): remitente no-reply@, HTML + texto y un correo por destinatario.

Django usa el backend en memoria durante las pruebas: nada sale a internet.
"""
import os
from unittest import skipIf

from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings

from apps.core.mail import absolute_url, send_email


@override_settings(SITE_URL="https://workspace.example.test", DEFAULT_FROM_EMAIL="Workspace <no-reply@example.test>")
class SendEmailTests(TestCase):
    def test_sends_html_and_text_from_no_reply(self):
        sent = send_email(to="ana@example.test", subject="Prueba", template="test", context={"name": "Ana"})
        self.assertEqual(sent, 1)
        message = mail.outbox[0]
        self.assertEqual(message.from_email, "Workspace <no-reply@example.test>")
        self.assertEqual(message.subject, "Prueba")
        self.assertIn("¡Hola, Ana!", message.body)                                 # versión de texto
        html, mimetype = message.alternatives[0]
        self.assertEqual(mimetype, "text/html")
        self.assertIn('href="https://workspace.example.test"', html)               # enlaces completos
        self.assertIn("no recibe respuestas", html)                                 # pie de la base

    def test_one_message_per_recipient_so_addresses_stay_private(self):
        sent = send_email(to=["ana@example.test", "", "beto@example.test"], subject="Aviso", template="test")
        self.assertEqual(sent, 2)
        self.assertEqual([m.to for m in mail.outbox], [["ana@example.test"], ["beto@example.test"]])

    def test_no_recipients_sends_nothing(self):
        self.assertEqual(send_email(to=[], subject="Nada", template="test"), 0)
        self.assertEqual(mail.outbox, [])

    def test_absolute_url(self):
        self.assertEqual(absolute_url("/forms/"), "https://workspace.example.test/forms/")
        self.assertEqual(absolute_url("forms/"), "https://workspace.example.test/forms/")
        self.assertEqual(absolute_url("https://otro.example/x"), "https://otro.example/x")


class MailSettingsTests(TestCase):
    @skipIf(os.getenv("DEFAULT_FROM_EMAIL"), "el .env define otro remitente")
    def test_default_sender_is_no_reply_of_company_domain(self):
        self.assertIn(f"no-reply@{settings.GOOGLE_ALLOWED_DOMAIN}", settings.DEFAULT_FROM_EMAIL)
        self.assertFalse(settings.SITE_URL.endswith("/"))
