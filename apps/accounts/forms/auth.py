from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    """Un solo campo para usuario o correo (lo resuelve ``UsernameOrEmailBackend``).

    El error no dice qué estuvo mal (usuario, correo o contraseña) para no revelar qué cuentas existen.
    """

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Usuario, correo o contraseña incorrectos.",
        "inactive": "Esta cuenta está desactivada. Contacta a Soporte TI.",
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].label = "Usuario o correo"
        self.fields["username"].max_length = 254
        self.fields["username"].widget.attrs["maxlength"] = 254
