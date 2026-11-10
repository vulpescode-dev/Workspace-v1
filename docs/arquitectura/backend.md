# Arquitectura del backend

Django 5.2 LTS + Django REST Framework. **Monolito modular** (no microservicios) que solo expone
**API** (`/api/`) y **administración** (`/admin/`). Las pantallas viven en `frontend/` (React).

## Estructura

```text
backend/
├── manage.py               # carga .env y elige config/settings/<DJANGO_ENV>.py
├── requirements.txt
├── .env / .env.example     # TODO lo que cambia entre equipos o servidores
├── config/
│   ├── env.py              # lectura de .env (env_str, env_bool, env_int, env_list)
│   ├── settings/           # base.py · development.py · production.py
│   ├── urls.py             # /admin/ y /api/ (nada más)
│   └── api.py              # raíz /api/, /api/health/ y montaje de cada app
├── apps/
│   ├── core/               # paquete (no app): paginación, validación de archivos, salud, correo
│   ├── accounts/           # User, roles/permisos, login JWT, perfiles, directorio, cumpleaños,
│   │                       # departamentos y organigrama (API en /api/org/)
│   ├── catalogs/           # datos compartidos: Emoji, BaseReaction
│   ├── social/             # Post, adjuntos, reacciones, comentarios, Follow
│   ├── notifications/      # Notification (avisos), PushSubscription
│   ├── blog/               # Article, categorías, reacciones, comentarios
│   ├── documents/          # Document, versiones, privacidad
│   ├── form_builder/       # DynamicForm, Question, Submission, Answer… (solo modelos)
│   ├── marketplace/        # Listing, ListingImage, ListingCategory
│   └── helpdesk/           # Ticket, comentarios, adjuntos, historial
├── templates/emails/       # única carpeta de plantillas: correos (HTML + texto)
├── static/assets/emoji/    # archivos Noto de los emojis del catálogo (la API entrega sus URLs)
├── media/                  # archivos subidos (privados: se entregan por vistas que validan permisos)
├── scripts/                # django-extensions runscript: bots/, generate_secret_key.py, fake_media.py, send_test_email.py…
└── tests/                  # por tipo (ver abajo)
```

### Dentro de cada app

| Carpeta | Qué va |
|---|---|
| `models/` | Modelos de datos. Nombres descriptivos (`PostCategory`, no `Category`). |
| `services/` | Operaciones que cambian estado o coordinan acciones (reglas de negocio). |
| `selectors/` | Consultas de lectura y visibilidad. |
| `api/` | `serializers.py`, `views.py`, `urls.py`. Vistas delgadas: validan entrada, llaman servicios/selectores. |
| `admin.py`, `apps.py`, `migrations/` | Lo estándar de Django. |

Sin capas vacías: si una app no necesita `services/`, no se crea.

## Decisiones vigentes

- **API única en `/api/`, sin versión** (`/api/v1/` no). Cada endpoint se documenta en `docs/backend/api.md`.
- **Autenticación JWT** (detalle en `docs/backend/autenticacion.md`). La sesión de Django queda solo para `/admin/` y la interfaz navegable en desarrollo.
- **Permisos en el servidor.** Roles de negocio propios (`app.recurso.accion[.all]`, p. ej. `social.posts.view.all`), independientes de los grupos de Django. Todo pasa por ellos: entrar a cada sección, crear, editar/borrar lo propio y moderar lo ajeno. Catálogo y roles semilla en `apps/accounts/data/` (se cargan al migrar); detalle en `docs/backend/permisos.md`. Ocultar un botón en React nunca es seguridad.
- **Migraciones:** una `0001_initial` por app (consolidadas en noviembre de 2026). `Department` vive en `accounts` junto a `User` (antes era la app `org`): se apuntan entre sí (área y jefe) y en apps separadas Django necesitaba una segunda migración. Su API sigue en `/api/org/`. Las cargas de datos van dentro de la migración: emojis (`catalogs`) y categorías iniciales de documentos (`documents`). Los permisos **no** se crean en migraciones: salen del catálogo.
- **Archivos:** validación por lista permitida y contenido real (`apps/core/uploads.py`); se guardan como `<id>.<ext>` y nunca se exponen rutas de `/media/` (ver `docs/backend/media-uploads.md`).
- **Paginación:** 25 por página, `?page_size=` hasta 25 (`SafePageNumberPagination`).
- **Fechas:** servidor en `America/Mexico_City`; la API manda ISO 8601 con desfase.
- **Base de datos:** SQLite en esta etapa; PostgreSQL más adelante (no basta con cambiar variables).
- **Sin** Docker, Redis, Celery ni WebSockets en esta etapa.
- **`.env` manda.** Nombre y código del proyecto, hosts permitidos, orígenes, base de datos, JWT, correo y Google salen de `backend/.env`. Los `.py` solo tienen valores por defecto.

## Variables de entorno

Ver `backend/.env.example` (comentado por secciones). Las principales:

| Variable | Uso |
|---|---|
| `PROJECT_NAME` | Nombre visible: raíz de la API, admin, remitente y asunto de correos. |
| `PROJECT_CODE` | Código corto: prefijo de cookies (`ws_sessionid`, `ws_refresh`…) y emisor de los JWT. |
| `DJANGO_ENV` | `development` o `production`. |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos (agregar la IP de la PC para probar desde el teléfono). |
| `FRONTEND_URL` | Origen de React: enlaces en correos y redirecciones. |
| `CORS_ALLOWED_ORIGINS` / `DJANGO_CSRF_TRUSTED_ORIGINS` | Solo si el frontend vive en otro dominio. |

## Pruebas

```bash
cd backend
.venv/Scripts/python manage.py test tests            # todas
.venv/Scripts/python manage.py test tests.auth       # solo un tipo
```

| Carpeta | Qué prueba |
|---|---|
| `tests/auth/` | JWT (login, refresh, rotación, logout, límite de intentos) y roles/permisos. |
| `tests/google/` | Reglas de «Continuar con Google» (dominio, correo verificado, cuentas desactivadas). |
| `tests/api/` | Endpoints por app: visibilidad, permisos, paginación, respuestas. |
| `tests/database/` | Modelos, restricciones y carga de catálogos. |
| `tests/uploads/` | Validación de archivos por contenido y entrega autorizada. |
| `tests/mail/` | Envío de correos (remitente, HTML + texto, un correo por destinatario). |
| `tests/core/` | Estructura del proyecto (solo API + admin, ajustes desde `.env`) y `/api/health/`. |

Una prueba nueva va en la carpeta de su **tipo**, no de su app. Si no encaja en ninguna, se crea una carpeta nueva con `__init__.py`.

## Catálogos y semillas

Se cargan solos con `migrate` y se pueden recargar a mano:

```bash
.venv/Scripts/python manage.py load_catalogs                # emojis de reacciones
.venv/Scripts/python manage.py load_permissions [--prune]   # permisos de negocio (accounts/data/permissions.json)
.venv/Scripts/python manage.py load_roles [--update]        # roles semilla (accounts/data/roles.json)
```

## Datos de desarrollo

```bash
.venv/Scripts/python manage.py runscript scripts.bots.create_bots    # 8 bots bot.* (contraseña «1234»)
.venv/Scripts/python manage.py runscript scripts.bots.create_posts
```

Solo corren con `DJANGO_ENV=development` (o `WORKSPACE_ALLOW_BOTS=1` a propósito).
