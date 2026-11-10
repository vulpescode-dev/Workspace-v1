"""Inicio de sesión con usuario **o** correo (mismo campo) y contraseña.

- Si lo escrito tiene «@» se busca por correo (sin distinguir mayúsculas); si no, por usuario.
- Las mismas protecciones que ``ModelBackend``: solo cuentas activas y el mismo tiempo de
  respuesta exista o no la cuenta (no deja averiguar qué usuarios o correos existen).
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class UsernameOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        identifier = (username or kwargs.get(User.USERNAME_FIELD) or "").strip()
        if not identifier or password is None:
            return None
        if "@" in identifier:
            user = User._default_manager.filter(email__iexact=identifier).first()
        else:
            user = User._default_manager.filter(**{User.USERNAME_FIELD: identifier}).first()
        if user is None:
            User().set_password(password)   # mismo costo que una contraseña real (anti-enumeración)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
