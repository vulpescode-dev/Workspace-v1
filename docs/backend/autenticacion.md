# Autenticación (JWT)

React se autentica contra la API con **JWT** (`djangorestframework-simplejwt`). No usa la sesión de Django.

## Cómo funciona

```text
React                                   Backend (/api/auth/)
─────                                   ────────────────────
POST login {username, password}  ───▶   valida (usuario o correo) ──▶ { access }  + cookie «<código>_refresh»
                                                                        (httpOnly, path=/api/auth/, SameSite=Strict)
GET /api/...  Authorization: Bearer <access>
   └─ 401 (access vencido) ──▶ POST refresh (con la cookie) ──▶ { access } + cookie nueva ──▶ reintenta
Recargar la página ─────────────▶ POST refresh ──▶ si responde, la sesión sigue; si no, /login
POST logout ─────────────────────▶ revoca el refresh y borra la cookie
```

| Token | Dónde vive | Duración (`.env`) | Para qué |
|---|---|---|---|
| **access** | Solo en memoria de React (`lib/api/token-store.ts`). Nunca en `localStorage` ni en cookies legibles. | `JWT_ACCESS_MINUTES` (60) | Va en cada petición. |
| **refresh** | Cookie **httpOnly** (JavaScript no la puede leer), solo se envía a `/api/auth/`. | `JWT_REFRESH_DAYS` (7) | Solo sirve para pedir otro access. **Se usa una vez**: cada refresh entrega uno nuevo y el anterior queda en la lista negra (`token_blacklist`). |

Por qué así:

- Un script inyectado (XSS) no puede robar el refresh (httpOnly) y el access dura poco.
- `SameSite=Strict` + `path=/api/auth/` evitan que otro sitio use la cookie (CSRF).
- En desarrollo Vite reenvía `/api` al backend: para el navegador todo es el mismo origen y no hace falta CORS.

## Configuración (`backend/.env`)

| Variable | Por defecto | Notas |
|---|---|---|
| `PROJECT_CODE` | `ws` | Prefijo de la cookie (`ws_refresh`) y emisor (`iss`) de los tokens. |
| `JWT_ACCESS_MINUTES` / `JWT_REFRESH_DAYS` | 60 / 7 | |
| `JWT_SIGNING_KEY` | vacía = `DJANGO_SECRET_KEY` | Cambiarla invalida todas las sesiones. |
| `JWT_COOKIE_SECURE` | `false` (producción: `true`) | Con HTTPS siempre `true`. |
| `JWT_COOKIE_SAMESITE` | `Strict` | Si el frontend vive en otro dominio habría que usar `None` + `Secure` + CORS. |
| `AUTH_THROTTLE_RATE` | `10/min` | Intentos de login por IP. |

## Archivos

- Backend: `apps/accounts/api/auth.py` (vistas), `apps/accounts/api/auth_urls.py`, ajustes `SIMPLE_JWT` y `JWT_REFRESH_COOKIE` en `config/settings/base.py`, login por usuario o correo en `apps/accounts/backends.py`.
- Frontend: `lib/api/client.ts` (Bearer + refresh automático, una sola petición aunque fallen varias a la vez), `lib/api/token-store.ts`, `features/auth/` (contexto, guards, formulario).
- Pruebas: `backend/tests/auth/test_jwt.py`.

## Pendiente

- **Google** (otra tanda): botón de Google Identity Services en React → `POST /api/auth/google/` que valide el token de Google con las reglas de dominio de `apps/accounts/adapters.py` y devuelva el mismo par de tokens.
- **Fotos protegidas:** las vistas de archivos piden el Bearer, así que React las descarga con `useProtectedImage` (blob). Con muchas imágenes (feed) convendrá evaluar URLs firmadas de corta duración.
- **Varias pestañas:** si dos pestañas hacen refresh al mismo tiempo con la misma cookie, la segunda pierde la sesión (rotación). Evaluar `BroadcastChannel` o un pequeño margen de gracia si se vuelve un problema real.
