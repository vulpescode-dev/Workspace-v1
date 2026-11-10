# Workspace

Intranet empresarial: publicaciones, avisos, documentos, formularios, mesa de ayuda y personas en un solo lugar.

```text
Workspace/
├── backend/    # Django 5.2 + DRF — solo API (/api/) y administración (/admin/)
├── frontend/   # React 19 + TypeScript + Vite + Tailwind CSS v4
├── docs/       # contexto, requisitos, checklist, arquitectura, API, permisos
└── .vscode/    # configuración compartida del editor (va en git)
```

Toda la documentación está en [`docs/`](docs/README.md). Lo que falta, en [`docs/checklist.md`](docs/checklist.md).

## Requisitos

- Python 3.13
- Node.js 24 (npm 11)

## Instalación (una sola vez)

### Backend

```bash
cd backend
py -3.13 -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
cp .env.example .env          # revisa y ajusta lo demás
.venv/Scripts/python manage.py runscript scripts.generate_secret_key   # escribe DJANGO_SECRET_KEY en .env
.venv/Scripts/python manage.py migrate
.venv/Scripts/python manage.py createsuperuser
```

> **`generate_secret_key` va justo después de `cp .env.example .env` y antes de `migrate`.** Genera una clave
> aleatoria y la guarda en `DJANGO_SECRET_KEY` de `backend/.env`. Solo la reemplaza si está vacía o sigue siendo
> la de ejemplo, así que correrlo de nuevo no hace nada. Para rotarla a propósito:
> `.venv/Scripts/python manage.py runscript scripts.generate_secret_key --script-args --force`
> (cierra todas las sesiones: los JWT firmados con la clave anterior dejan de valer). Cada equipo o servidor
> tiene su propia clave; nunca la subas al repositorio.

En macOS/Linux usa `python3.13 -m venv .venv` y `.venv/bin/python`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
```

## Correr la app (cada vez)

Dos terminales:

```bash
cd backend
.venv/Scripts/python manage.py runserver
```

```bash
cd frontend
npm run dev
```

Abre **<http://localhost:5173>**. Vite reenvía `/api`, `/media` y `/static` al backend (`:8000`), así que el
navegador ve un solo origen. El admin sigue en <http://localhost:8000/admin/>.

### Correr en la red (abrirla desde el teléfono u otra PC)

Para que otros equipos de la misma red entren con la IP de tu PC (p. ej. `192.168.1.50`; la ves con
`ipconfig`, «Dirección IPv4»):

1. En `backend/.env` agrega tu IP a los hosts permitidos y úsala como origen del frontend:

   ```
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,[::1],192.168.1.50
   FRONTEND_URL=http://192.168.1.50:5173
   ```

   Hace falta aunque el backend siga en `localhost`: Vite le reenvía las peticiones con la dirección que
   escribió el otro equipo y Django rechaza las IP que no están en la lista. `FRONTEND_URL` hace que los
   enlaces de los correos apunten a tu IP.

2. Backend, igual que siempre (todo pasa por Vite):

   ```bash
   cd backend
   .venv/Scripts/python manage.py runserver
   ```

3. Frontend escuchando en la red:

   ```bash
   cd frontend
   npm run dev -- --host
   ```

   Vite muestra la dirección «Network» (p. ej. `http://192.168.1.50:5173`): ábrela desde el otro equipo.

Notas:

- La primera vez Windows puede pedir permiso en el firewall para Node: permite **redes privadas**.
- `FRONTEND_ALLOWED_HOSTS` (en `frontend/.env`) solo hace falta si entras con un nombre (p. ej. `mi-pc.local`);
  con la IP no.
- Para abrir el admin desde otro equipo arranca el backend con `runserver 0.0.0.0:8000` y entra a
  `http://192.168.1.50:8000/admin/`.
- Si tu IP cambia (otra red Wi-Fi), actualiza los dos valores del paso 1.

## Datos de prueba

```bash
cd backend
.venv/Scripts/python manage.py runscript scripts.bots.create_bots     # 8 bots bot.* — contraseña «1234»
.venv/Scripts/python manage.py runscript scripts.bots.create_posts    # publicaciones con reacciones y comentarios
```

Bots: `bot.ana`, `bot.beto`, `bot.carla`, `bot.diego`, `bot.elena`, `bot.fer`, `bot.gabo`, `bot.irene`
(también entran con su correo, p. ej. `bot.ana@workspace.test`). Solo corren en desarrollo.

Tras `migrate` se cargan solos los emojis de las reacciones, el catálogo de permisos y los roles básicos (Lector,
Influencer, Vendedor y Solicitante de soporte, que reciben todos los usuarios nuevos; y Blogger). Para recargarlos:
`manage.py load_catalogs`, `load_permissions` y `load_roles` (ver [`docs/backend/permisos.md`](docs/backend/permisos.md)).
Los usuarios creados **antes** de existir un rol por defecto no lo reciben solos: admin → Roles → «Asignar a todos
los usuarios activos».

## Pruebas y verificación

```bash
cd backend && .venv/Scripts/python manage.py test tests      # todas (o tests.auth, tests.api…)
cd frontend && npm run build && npm run lint && npm test
```

## Git

Hay un `.gitignore` en la raíz (lo común a todo el proyecto), uno en `backend/` y otro en `frontend/`.
**Nunca** se suben: `.env` (llaves y contraseñas), `db.sqlite3`, `media/` (archivos de las personas), `.venv/`,
`node_modules/` ni `dist/`. Sí se suben: los `.env.example`, las migraciones, los catálogos de `data/` y `.vscode/`.

## Configuración

Todo lo que cambia entre equipos o servidores va en `.env` (nunca en el código ni en el repositorio):

- `backend/.env` — nombre y código del proyecto, entorno, hosts permitidos, origen del frontend, base de datos, JWT, correo, Google. Ver `backend/.env.example`.
- `frontend/.env` — nombre y código del proyecto, URL de la API y opciones del servidor de desarrollo. Ver `frontend/.env.example`.
