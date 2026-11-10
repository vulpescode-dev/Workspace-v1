"""Autenticación de la API con JWT (djangorestframework-simplejwt).

- ``POST /api/auth/login/`` ``{"username", "password"}`` (usuario **o** correo): responde ``{"access"}``
  y deja el refresh token en una cookie httpOnly (``JWT_REFRESH_COOKIE``), limitada a ``/api/auth/``.
- ``POST /api/auth/refresh/``: con esa cookie entrega otro ``access`` y rota la cookie (cada refresh
  se usa una sola vez; el anterior queda en la lista negra).
- ``POST /api/auth/logout/``: revoca el refresh de la cookie y la borra. Siempre responde 204.

El access token nunca se guarda en cookie ni en ``localStorage``: React lo tiene solo en memoria y,
al recargar la página, pide uno nuevo con ``/refresh/``.
"""
from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken


def _refresh_cookie_name() -> str:
    return settings.JWT_REFRESH_COOKIE["key"]


def _with_refresh_cookie(response: Response, refresh: str) -> Response:
    cookie = settings.JWT_REFRESH_COOKIE
    response.set_cookie(
        cookie["key"], refresh,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        path=cookie["path"], httponly=cookie["httponly"], secure=cookie["secure"], samesite=cookie["samesite"],
    )
    return response


def _without_refresh_cookie(response: Response) -> Response:
    cookie = settings.JWT_REFRESH_COOKIE
    response.delete_cookie(cookie["key"], path=cookie["path"], samesite=cookie["samesite"])
    return response


class _PublicAuthView(APIView):
    """Sin sesión ni JWT previos (y por lo tanto sin CSRF de sesión); con límite de intentos por IP."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def get_authenticate_header(self, request):
        return 'Bearer realm="api"'   # sin esto DRF convierte los 401 en 403


class LoginView(_PublicAuthView):
    def post(self, request):
        serializer = TokenObtainPairSerializer(data=request.data, context={"request": request})
        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed:
            raise AuthenticationFailed("Usuario o contraseña incorrectos.") from None
        tokens = serializer.validated_data
        return _with_refresh_cookie(Response({"access": tokens["access"]}), tokens["refresh"])


class RefreshView(_PublicAuthView):
    throttle_classes = []   # se llama en cada recarga de página; sin cookie válida no sirve de nada

    def post(self, request):
        refresh = request.COOKIES.get(_refresh_cookie_name())
        if not refresh:
            raise AuthenticationFailed("No hay sesión activa.")
        serializer = TokenRefreshSerializer(data={"refresh": refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, AuthenticationFailed):
            response = Response({"detail": "La sesión expiró. Vuelve a iniciar sesión."}, status=status.HTTP_401_UNAUTHORIZED)
            return _without_refresh_cookie(response)
        tokens = serializer.validated_data
        response = Response({"access": tokens["access"]})
        return _with_refresh_cookie(response, tokens.get("refresh", refresh))


class LogoutView(_PublicAuthView):
    throttle_classes = []

    def post(self, request):
        refresh = request.COOKIES.get(_refresh_cookie_name())
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except TokenError:
                pass   # ya vencido o revocado: no hay nada que cerrar
        return _without_refresh_cookie(Response(status=status.HTTP_204_NO_CONTENT))
