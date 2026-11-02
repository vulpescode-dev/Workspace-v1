# Workspace

**Workspace** es la intranet de la empresa, hecha primero para el celular: publicaciones, avisos, personas
y perfiles hoy; noticias (blog), marketplace, mesa de ayuda, documentos y formularios en camino. No es solo una red social ni solo una intranet: une
la capa social, la intranet (avisos, documentos, áreas) y herramientas de productividad (formularios) en una
sola app web. La visión completa y las reglas de diseño están en [`AGENT.md`](AGENT.md).

> **Estado:** en desarrollo, por tandas. Lo hecho y lo pendiente vive en [`docs/backlog.md`](docs/backlog.md).

| Funciona | En camino | Pendiente |
|---|---|---|
| Login con usuario o correo (y Google @orienta.soy al poner credenciales) · Muro con fotos/videos, reacciones con 134 emojis animados, comentarios y respuestas · Perfiles y seguidores · Directorio (filtros por departamento, género y estado civil) · Organigrama · Avisos (API completa: leídas, contador, dispositivos push) · Inicio en 3 columnas en escritorio (menú, publicaciones, widgets) · `/api/health/` | **API lista, faltan pantallas:** Blog / Noticias · Marketplace · Mesa de ayuda · Documentos (categorías, privacidad y versiones). **Modelos listos:** Formularios (estilo Google Forms) | Búsqueda real · Envío de push · Buzón (feedback) |

**Tecnologías:** Python · Django 5.2 LTS · Django REST Framework · Bootstrap 5.3 · jQuery · Day.js ·
SQLite (desarrollo) · django-allauth (Google) · django-extensions (scripts) · nh3 (HTML seguro).

---

## 1. Requisitos

- **Python 3.12 o 3.13** (probado con 3.13).
- **Git**.
- Nada más: SQLite viene con Python. No hace falta Docker, PostgreSQL ni Node.

<details>
<summary><strong>Windows</strong>: instalar Python y Git</summary>

1. Descarga Python desde <https://www.python.org/downloads/windows/> y, en el instalador, marca
   **Add python.exe to PATH**.
2. Descarga Git desde <https://git-scm.com/download/win>.
3. Abre **PowerShell** y comprueba:

   ```powershell
   python --version
   git --version
   ```

   Si `python` abre la Microsoft Store: *Configuración → Aplicaciones → Configuración avanzada de
   aplicaciones → Alias de ejecución de aplicaciones* y apaga los de `python.exe` y `python3.exe`.
</details>

<details>
<summary><strong>macOS</strong>: instalar Python y Git</summary>

1. Instala Python desde <https://www.python.org/downloads/macos/> (o con Homebrew: `brew install python@3.13`).
2. Git viene con las herramientas de desarrollo de Apple; si no lo tienes, `xcode-select --install`.
3. Abre **Terminal** y comprueba:

   ```bash
   python3 --version
   git --version
   ```

   En macOS se usa `python3` para crear el entorno; ya dentro del entorno basta con `python`.
</details>

## 2. Instalación (una sola vez)

El repositorio es **privado**: necesitas que te den acceso en GitHub. Al clonar, Git te pedirá iniciar sesión
(en Windows abre una ventana; en macOS usa un *token* de GitHub como contraseña o `gh auth login`).

### Windows (PowerShell)

```powershell
git clone https://github.com/vulpescode-dev/Workspace-v1.git
cd Workspace-v1

python -m venv .venv
.\.venv\Scripts\Activate.ps1          # verás (.venv) al inicio de la línea

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser      # tu cuenta de administrador
```

Si PowerShell no deja activar el entorno («la ejecución de scripts está deshabilitada»), ejecuta una vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y vuelve a activarlo.

### macOS (Terminal)

```bash
git clone https://github.com/vulpescode-dev/Workspace-v1.git
cd Workspace-v1

python3 -m venv .venv
source .venv/bin/activate              # verás (.venv) al inicio de la línea

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

cp .env.example .env
python manage.py migrate
python manage.py createsuperuser       # tu cuenta de administrador
```

`migrate` crea la base de datos (`db.sqlite3`) y **ya carga los 134 emojis** de las reacciones; no hay pasos extra.
Si algún día se pierden, se recuperan con `load_catalogs` (sección 4).

### El archivo `.env`

`.env` guarda la configuración local y **nunca se sube a Git** (está en `.gitignore`). Para desarrollar
basta con la copia de `.env.example`. Lo que puedes ajustar:

| Variable | Para qué | Valor de ejemplo |
|---|---|---|
| `DJANGO_SECRET_KEY` | Clave secreta. En desarrollo se usa una de prueba si está vacía; **en producción es obligatoria**. | ver comando abajo |
| `DJANGO_ALLOWED_HOSTS` | Direcciones con las que se puede abrir la app, separadas por coma. Agrega la IP de tu PC para entrar desde el teléfono (sección 6). | `localhost,127.0.0.1` |
| `DJANGO_TIME_ZONE` | Zona del servidor (la sede está en Querétaro). Cada navegador ve las horas en su propia zona. | `America/Mexico_City` |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | «Continuar con Google». Vacías: el botón aparece deshabilitado (ver sección 7). | — |
| `GOOGLE_ALLOWED_DOMAIN` | Solo cuentas de este dominio entran con Google. | `orienta.soy` |
| `WEBPUSH_VAPID_PUBLIC_KEY` | Llave pública para notificaciones push de la PWA. Vacía: push desactivado. | — |

Generar una clave secreta:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 3. Correr la app (cada vez)

Activa el entorno y arranca el servidor:

```powershell
# Windows
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

```bash
# macOS
source .venv/bin/activate
python manage.py runserver
```

Abre **<http://localhost:8000/>** e inicia sesión con tu usuario **o** tu correo. Detén el servidor con `Ctrl+C`.

| Dirección | Qué es |
|---|---|
| <http://localhost:8000/> | La app (pide iniciar sesión) |
| <http://localhost:8000/admin/> | Administración de Django (usuarios, roles y permisos, departamentos, categorías, emojis…). En el menú de cuenta solo aparece para superusuarios. |
| <http://localhost:8000/api/> | Raíz de la API REST (todas las APIs y cómo probarlas: [`docs/api.md`](docs/api.md)) |
| <http://localhost:8000/api/health/> | Salud de la app: base de datos, migraciones, archivos y datos base (200 = bien, 503 = algo falla) |
| <http://localhost:8000/search/> · `/calendar/` · `/people/` · `/notifications/` | Buscar, Calendario, Personas y Avisos |
| `/blog/` · `/documents/` · `/forms/` · `/marketplace/` · `/helpdesk/` · `/help/` | Secciones en construcción (página con aviso) |
| <http://localhost:8000/showcase/> | Presentación comercial (solo en desarrollo, sección 6) |
| `/terms/` · `/privacy/` | Términos y Privacidad (públicas: se ven sin iniciar sesión) |
| `/manifest.webmanifest` | Manifest de la app instalable (PWA) |

> Después de cambiar el archivo `.env`, reinicia el servidor: solo lo lee al arrancar.

## 4. Datos: emojis y bots de prueba

### Emojis de las reacciones (`load_catalogs`)

Los 134 emojis no dependen solo de la base ni de las migraciones: viven en
`apps/catalogs/data/emojis.json`, dentro del repositorio. Si se pierden (base nueva, migraciones
regeneradas, tabla borrada por error) o si editaste ese JSON, vuelve a cargarlos con:

```bash
python manage.py load_catalogs
```

Salida esperada: `Emojis: 0 creados, 0 actualizados, 0 desactivados.` (los números cambian si había algo que
cargar).

- Es un comando de Django: se corre con el entorno activo, desde la carpeta del proyecto (donde está
  `manage.py`). No hace falta tener `runserver` corriendo, solo haber hecho `migrate`.
- **Se puede correr cuantas veces quieras:** crea los que faltan y actualiza los que cambiaron; nunca duplica.
- **No borra nada:** un emoji que se quita del JSON se desactiva, para no romper las reacciones que ya lo usan.
- **El JSON manda:** si desactivaste un emoji en el admin pero en el JSON sigue activo, este comando lo vuelve a
  activar. Para que sea permanente, cámbialo también en el JSON (`"active": false`).
- **Red de seguridad:** si después de un `migrate` la tabla de emojis queda vacía, se llena sola desde el JSON.
- Para revisar: <http://localhost:8000/api/health/> debe decir `"catalogs": "ok"`.
- Agregar o cambiar emojis: [`docs/reaction-emojis.md`](docs/reaction-emojis.md).

### Datos de prueba: bots

Para no ver la app vacía hay scripts (en `scripts/bots/`) que crean **8 bots** con personalidad propia y
llenan el muro. Solo funcionan en desarrollo (con `DEBUG=True`); con `DEBUG=False` se niegan a correr salvo
que pongas a propósito `WORKSPACE_ALLOW_BOTS=1` (p. ej. un servidor de pruebas, nunca producción).

```bash
python manage.py runscript scripts.bots.create_bots                    # crea/reutiliza los 8 bots y sus seguimientos
python manage.py runscript scripts.bots.create_posts                   # 24 publicaciones con reacciones y comentarios
python manage.py runscript scripts.bots.create_posts --script-args 40  # otra cantidad
```

| Usuario | Nombre | Cargo · Área |
|---|---|---|
| `bot.ana` | Ana Robles | Diseñadora UX · Producto |
| `bot.beto` | Beto Sáenz | Desarrollador backend · Tecnología |
| `bot.carla` | Carla Méndez | Coordinadora de Capital Humano · Recursos Humanos |
| `bot.diego` | Diego Fuentes | Analista de datos · Finanzas |
| `bot.elena` | Elena Vargas | Líder de Soporte TI · Tecnología |
| `bot.fer` | Fernanda Ortiz | Ejecutiva de ventas · Comercial |
| `bot.gabo` | Gabriel Luna | Coordinador de Operaciones · Operaciones |
| `bot.irene` | Irene Castañeda | Abogada corporativa · Legal |

- **Contraseña de todos: `1234`.** También puedes entrar con su correo, p. ej. `bot.ana@workspace.test`.
- Los bots se buscan por usuario: correr `create_bots` otra vez no los duplica ni les cambia nada.
- Sus cumpleaños quedan cerca de la fecha en que se crean, para que se vea el widget de cumpleaños.
- Quiénes son, qué temas tocan, cómo escriben (frases, emojis, largo) y a quién siguen está en
  `scripts/bots/personas.py`. Entre bots siguen exactamente lo que dice ese archivo (no todos se siguen ni
  todo es recíproco); algunos siguen a administración (cuentas con `is_superuser`) y a unas cuantas personas
  reales. Nunca se cambia lo que siguen las personas reales.
- `create_posts` publica con la voz de cada bot: solo texto, 1 a 10 imágenes (generadas, no se descarga
  nada), solo imágenes y algunas «Solo seguidores». Reacciones, comentarios y respuestas solo de quien puede
  ver la publicación y no en todas. **Cada vez que lo corres agrega publicaciones nuevas** (más recientes que
  las existentes) sin borrar las anteriores.
- Para empezar de cero en desarrollo: borra `db.sqlite3` y la carpeta `media/` (fotos subidas; Django la
  vuelve a crear sola) y corre otra vez `migrate`, `createsuperuser` y los scripts.

### Escribir tus propios scripts

Cada archivo `scripts/<nombre>.py` con una función `run()` se ejecuta con Django ya cargado:

```python
# scripts/mi_script.py
from scripts.bots.create_bots import get_bots   # los mismos 8 bots
from scripts.fake_media import photo            # imágenes WebP de relleno


def run(*args):
    ana, beto, carla, diego, elena, fer, gabo, irene = get_bots()
    ...
```

```bash
python manage.py runscript mi_script
python manage.py runscript mi_script --script-args valor1 valor2
```

## 5. Pruebas

```bash
python manage.py test tests
```

Todas deben pasar antes de subir cambios.

**Migraciones.** Cada app parte de una sola migración inicial (`0001_initial`), que ya incluye sus datos base
(emojis en `catalogs`, permisos de negocio en `helpdesk` y `documents`). La excepción es `accounts`, que tiene
dos: `accounts` y `org` se apuntan entre sí (el usuario tiene departamento y el departamento tiene responsable),
así que `0002_user_department` va después de crear `org`. Si cambias un modelo:

```bash
python manage.py makemigrations     # crea la migración nueva de esa app
python manage.py migrate
```

y sube la migración junto con el cambio. No borres ni edites migraciones que ya se subieron: otras personas
ya las aplicaron.

## 6. Presentación (`showcase.html`)

`showcase.html`, en la raíz, presenta la app dentro de un iPhone. Es independiente (todo por CDN). En
desarrollo, Django la sirve en **<http://localhost:8000/showcase/>**: mismo sitio que la app, así que se puede
**iniciar sesión dentro del teléfono**, y cada cambio al archivo se ve con solo recargar.

Para que el **QR** funcione en tu teléfono (misma red Wi-Fi):

1. Agrega la IP de tu PC en `.env`: `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.50`.
2. Arranca Django para la red: `python manage.py runserver 0.0.0.0:8000`.
3. Abre la presentación por esa IP: `http://192.168.1.50:8000/showcase/`. Teléfono, QR y enlaces usan la
   dirección con la que la abriste; no hay que editar el archivo.

- Con doble clic (`file://`) el navegador no le pasa la sesión al teléfono y el login falla (error CSRF). La
  presentación lo detecta y lo explica en pantalla.
- También se puede servir aparte (`python -m http.server 5500 --bind 127.0.0.1` → `http://localhost:5500/showcase.html`):
  usa el mismo host en el puerto 8000. `--bind 127.0.0.1` importa: ese servidor expone toda la carpeta
  (incluidos `db.sqlite3` y `.env`).
- Para una dirección fija (prueba, oficial): pon `APP_URL` en el archivo o abre `showcase.html?app=https://...`.

## 7. Iniciar sesión con Google (opcional)

El botón «Continuar con Google» ya está programado y **solo deja entrar cuentas `@orienta.soy`**. Falta que el
responsable de Google Workspace de la empresa cree las credenciales:

1. En Google Cloud: *APIs y servicios → Credenciales → Crear ID de cliente OAuth* → **Aplicación web**, con
   pantalla de consentimiento **Interna**.
2. URI de redirección autorizados:
   - `http://localhost:8000/accounts/google/login/callback/` (desarrollo)
   - `https://<dominio>/accounts/google/login/callback/` (producción)
3. Pon `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` en `.env` y reinicia el servidor.

La primera vez que alguien entra con Google se crea su cuenta; si ya existía una con ese correo, se vincula.

## 8. Correo (preparado)

Los correos salen con el remitente **`Workspace <no-reply@orienta.soy>`** (usa `GOOGLE_ALLOWED_DOMAIN`). La cuenta
aún no existe, así que **mientras no haya servidor SMTP los correos se imprimen en la consola** del servidor.

```bash
python manage.py runscript send_test_email --script-args tu@correo.com   # correo de prueba con la plantilla
python manage.py sendtestemail tu@correo.com                              # prueba la conexión SMTP (cuando exista)
```

Cuando exista la cuenta: pon `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (contraseña de
aplicación, nunca la personal) y `SITE_URL` en `.env` (ver `.env.example`). En producción basta con `EMAIL_HOST`
para que use SMTP; en desarrollo, además `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`.
Desde el código: `from apps.core.mail import send_email` (plantillas en `templates/emails/`).

## 9. App instalable (PWA)

Workspace tiene manifest (`/manifest.webmanifest`) e íconos, así que se puede instalar: en Chrome para Android
aparece «Instalar app» / «Agregar a pantalla principal»; en computadora, el ícono de instalar en la barra de
direcciones; en iPhone, *Compartir → Agregar a pantalla de inicio*. Requiere **HTTPS** (o `localhost`); desde
el teléfono por la IP de tu computadora (`http://192.168…`) no se ofrece. Si cambia el logo:
`python manage.py runscript make_icons`. Pendiente: service worker (sin conexión y notificaciones push).

## 10. Problemas frecuentes

| Problema | Solución |
|---|---|
| `No module named 'django'` | El entorno no está activo: actívalo (sección 3) y, si hace falta, `pip install -r requirements.txt`. |
| PowerShell: «la ejecución de scripts está deshabilitada» | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y vuelve a activar. |
| `python` abre la Microsoft Store (Windows) | Apaga los alias de ejecución de `python.exe` (sección 1). |
| macOS: `command not found: python` | Fuera del entorno usa `python3`; dentro de `(.venv)` ya funciona `python`. |
| `no such table` | Faltan migraciones: `python manage.py migrate`. |
| `InconsistentMigrationHistory` al hacer `migrate` | Tu `db.sqlite3` es de antes de que se unificaran las migraciones. En desarrollo: borra `db.sqlite3` y `media/`, y corre otra vez `migrate` y `createsuperuser` (sección 4). |
| `DisallowedHost` / «Bad Request (400)» desde el teléfono | Agrega la IP de tu PC a `DJANGO_ALLOWED_HOSTS` en `.env`, reinicia y arranca con `runserver 0.0.0.0:8000`. |
| No aparecen emojis para reaccionar | `python manage.py load_catalogs` (y revisa <http://localhost:8000/api/health/>). |
| 403 «CSRF» al iniciar sesión | Recarga la página de login. Si es en la presentación, ábrela desde `/showcase/` en el mismo Django, no con doble clic (sección 6). |
| No ves un cambio de CSS/JS | Recarga normal: en desarrollo los archivos llevan `?v=<versión>` y el navegador pide la nueva. |
| La hora sale distinta | Es correcto: cada quien ve la hora de su zona. La del servidor se cambia con `DJANGO_TIME_ZONE`. |
| `runscript`: «solo para desarrollo» | Los bots solo corren con `DEBUG=True` (configuración de desarrollo, la predeterminada de `manage.py`) o con `WORKSPACE_ALLOW_BOTS=1`. |

## 11. Mapa del proyecto

```text
Workspace-v1/
├── manage.py
├── requirements.txt · .env.example · showcase.html
├── config/                 # settings (base, development, production), urls, raíz de la API
├── apps/
│   ├── accounts/           # usuario, login (usuario/correo y Google), perfiles, directorio, cumpleaños
│   ├── social/             # publicaciones, adjuntos, reacciones, comentarios, seguidores
│   ├── notifications/      # avisos y dispositivos push (API)
│   ├── catalogs/           # datos compartidos (emojis) y el comando load_catalogs
│   ├── blog/               # noticias (modelos + API)
│   ├── marketplace/        # compra-venta entre compañeros (modelos + API)
│   ├── form_builder/       # formularios (modelos)
│   ├── documents/          # documentos: categorías, privacidad y versiones (modelos + API)
│   ├── helpdesk/           # mesa de ayuda: tickets por departamento (modelos + API)
│   ├── org/                # departamentos y organigrama
│   └── core/               # utilidades: paginación, archivos, estáticos con versión, salud, páginas generales, PWA, correo
├── templates/              # TODAS las plantillas (layouts, pages, components, emails)
├── static/assets/          # css, js, emojis, íconos (img/icons), librerías locales (vendor)
├── scripts/                # runscript: bots, íconos de la app, correo de prueba
├── tests/                  # pruebas automáticas
└── docs/                   # arquitectura, backlog y notas técnicas
```

## 12. Documentación

- [`AGENT.md`](AGENT.md): visión del producto, decisiones y convenciones (léelo antes de programar).
- [`docs/api.md`](docs/api.md): **todas las APIs** (qué hay, cómo verlas en el navegador, filtros y paginación).
- [`docs/architecture.md`](docs/architecture.md): arquitectura, API y estado de cada módulo.
- [`docs/backlog.md`](docs/backlog.md): qué está hecho y qué falta, por tandas.
- [`docs/media-uploads.md`](docs/media-uploads.md): fotos y videos (validación y entrega segura).
- [`docs/reaction-emojis.md`](docs/reaction-emojis.md): catálogo de emojis y cómo agregar más.
