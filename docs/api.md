# API de Workspace

Todas las APIs del proyecto en un solo lugar: qué hay, cómo verlas en el navegador y cómo llamarlas.
Si agregas o cambias un endpoint, **actualiza este archivo** (y la raíz `/api/` en `config/api.py`).

## 1. Cómo verlas en el navegador

1. Levanta el servidor: `python manage.py runserver`.
2. Inicia sesión en **<http://localhost:8000/accounts/login/>** (cualquier usuario; en desarrollo
   sirven los bots, p. ej. `bot.ana` / `1234`).
3. Entra a **<http://localhost:8000/api/>**: es la raíz, con enlaces a cada sección. Desde ahí, o
   escribiendo cualquier URL de las tablas de abajo, Django REST Framework muestra la **interfaz
   navegable**: el JSON con formato, los métodos permitidos y, abajo, un formulario para probar
   `POST` / `PUT` / `PATCH` / `DELETE`.

Notas:

- La interfaz navegable solo existe en **desarrollo** (`config/settings/development.py`). En producción
  la API responde únicamente JSON.
- Sin sesión, todo responde **403** (excepto la raíz `/api/` y `/api/health/`).
- Para ver solo el JSON agrega `?format=json` (p. ej. <http://localhost:8000/api/social/posts/?format=json>).
- Lista completa de rutas desde la terminal (django-extensions):

  ```bash
  python manage.py show_urls
  ```

## 2. Reglas comunes

| Tema | Regla |
|---|---|
| Raíz | Única base `/api/`, **sin versión** (nada de `/api/v1/`). |
| Autenticación | Sesión de Django (la misma cookie que la app). No hay tokens. |
| CSRF | Todo lo que no sea `GET` necesita el encabezado `X-CSRFToken` (lo pone `Workspace.api` en `workspace.js`). |
| Paginación | Todas las listas: `?page=<n>` y `?page_size=<n>` (**25 por omisión y máximo 25**; más de 25 se limita a 25, un valor inválido usa 25). Respuesta: `{"count", "page", "total_pages", "next", "previous", "results"}`. Una página inexistente responde 404 con `count` y `total_pages`. Solo los catálogos cortos (emojis, categorías) no se paginan. |
| Errores | `400` con `{"campo": ["mensaje"]}`; `403` sin permiso (p. ej. editar algo ajeno); `404` si no existe, está eliminado o no lo puedes ver. |
| Archivos | Fotos y videos nunca salen de `/media/`: cada uno tiene su endpoint `…/file/` o `…/cover/` que revisa si lo puedes ver. Se suben en **multipart**; imágenes solo **WebP** (el navegador convierte antes de subir, ver `docs/media-uploads.md`). |
| Reacciones | Una por persona. `PUT {"emoji": "<código>"}` pone o cambia, `DELETE` quita; ambos responden el resumen `{"reactions": [{"emoji", "count"}], "total", "mine"}`. Códigos en `/api/catalogs/emojis/`. |
| Comentarios | Respuestas de un nivel (`parent`), borrado suave; un raíz eliminado con respuestas vivas sale como `is_deleted: true`. |
| Fechas | ISO 8601 con zona (`2026-10-28T10:30:00-06:00`). |

## 3. Endpoints

### Raíz

| Método | URL | Qué hace |
|---|---|---|
| GET | [`/api/`](http://localhost:8000/api/) | Nombre de la API y enlaces a cada sección. Abierta sin sesión. |

### Salud — `config/api.py` + `apps/core/health.py`

| Método | URL | Qué hace |
|---|---|---|
| GET | [`/api/health/`](http://localhost:8000/api/health/) | ¿Está viva la app? Abierta **sin sesión** (para monitores de disponibilidad y balanceadores). |

Responde **200** si todo está bien y **503** si algo falla, con `ok` / `error` por comprobación:

| Comprobación | Qué revisa |
|---|---|
| `database` | La base de datos responde a una consulta mínima. |
| `migrations` | No hay migraciones sin aplicar. |
| `storage` | La carpeta de archivos subidos (`MEDIA_ROOT`) existe y se puede escribir. |
| `catalogs` | Los datos base están cargados (emojis activos). |

```json
{"status": "ok", "checks": {"database": "ok", "migrations": "ok", "storage": "ok", "catalogs": "ok"}, "time": "2026-10-28T22:54:57-06:00"}
```

Con sesión de **personal** (`is_staff`, p. ej. el admin) agrega `details` (tiempo de respuesta de la
base, migraciones pendientes, mensaje de error), `apps` (apps de Workspace instaladas) y
`environment` (DEBUG, settings, versión de Django y Python). A los demás no se les muestra para no
exponer información interna. Para agregar una comprobación: una función más en `CHECKS` de
`apps/core/health.py`.

### Cuentas — `apps/accounts/api/`

| Método | URL | Qué hace |
|---|---|---|
| GET | [`/api/accounts/me/`](http://localhost:8000/api/accounts/me/) | Mi perfil. Incluye `department` (nombre), `department_id` y `manager` (jefe directo en forma corta, o `null`). |
| PATCH | `/api/accounts/me/` | `{"bio"}`: cambia mi presentación (lo demás lo administra RRHH/TI). |
| POST / DELETE | `/api/accounts/me/avatar/` | Multipart `file` (WebP): cambia mi foto / la quita. |
| GET | [`/api/accounts/users/`](http://localhost:8000/api/accounts/users/) | Directorio de personas activas. `?search=<texto>` (nombre, correo, cargo o departamento), `?department=<id>`, `?gender=male|female`, `?marital_status=single|in_relationship|married|common_law|divorced|widowed|complicated`. Se combinan entre sí y con la paginación; un valor que no existe responde 400. La respuesta no incluye género ni estado civil. |
| GET | `/api/accounts/users/<id>/` | Perfil de una persona. |
| GET | `/api/accounts/users/<id>/avatar/` | Foto de una persona. |
| GET | [`/api/accounts/birthdays/`](http://localhost:8000/api/accounts/birthdays/) | Cumpleaños de hoy y los próximos 30 días (máx. 6). |

### Catálogos — `apps/catalogs/api/`

| Método | URL | Qué hace |
|---|---|---|
| GET | [`/api/catalogs/emojis/`](http://localhost:8000/api/catalogs/emojis/) | Emojis activos para reaccionar (sin paginar). |

### Organización — `apps/org/api/`

Departamentos y organigrama. Se administran en el admin (RRHH/TI); la API solo los lee.

| Método | URL | Qué hace |
|---|---|---|
| GET | [`/api/org/departments/`](http://localhost:8000/api/org/departments/) | Departamentos activos por nombre (sin paginar): `id`, `name`, `description`, `parent_id` (subárea de), `head` (responsable o `null`), `members_count`. |
| GET | `/api/org/departments/<id>/` | Un departamento. Sus personas: `/api/accounts/users/?department=<id>`. |
| GET | [`/api/org/chart/`](http://localhost:8000/api/org/chart/) | Organigrama por jefe directo. `?root=<id de persona>` (solo desde esa persona), `?depth=<n>` (3 por omisión, máx. 10). |

```json
{"depth": 3, "unassigned_count": 4, "roots": [
  {"id": 1, "name": "Carla Méndez", "initials": "CM", "avatar_url": "", "job_title": "Dirección general",
   "department": {"id": 3, "name": "Dirección"}, "reports_count": 2, "children": [ … ]}
]}
```

Raíces: quien no tiene jefe activo y sí tiene personas a cargo. `reports_count` dice cuántas personas
tiene a cargo aunque `children` venga vacío por la profundidad (para cargar más con `?root=`).
`unassigned_count`: personas sin jefe ni personas a cargo (falta completarlas en el admin).

### Mesa de ayuda — `apps/helpdesk/api/`

Una persona levanta un ticket eligiendo una **categoría**; el ticket llega al **departamento** de esa
categoría. Lo atienden sus **agentes**: el responsable del departamento y quienes sean de ese
departamento con el permiso de negocio `helpdesk.tickets.attend` (un superusuario atiende todos).
`helpdesk.tickets.view.all` permite consultar todos los tickets sin atenderlos. Ambos permisos ya
existen (migración); se asignan a un rol en el admin. Las categorías se crean en el admin.

| Método | URL | Qué hace |
|---|---|---|
| GET | [`/api/helpdesk/me/`](http://localhost:8000/api/helpdesk/me/) | `{"attends": [{id, name}], "all_departments", "view_all"}`: qué departamentos atiendo. |
| GET | [`/api/helpdesk/categories/`](http://localhost:8000/api/helpdesk/categories/) | Categorías que se pueden elegir (sin paginar), con su departamento y `kind` (`incident` / `request`). `?department=<id>`. |
| GET | [`/api/helpdesk/tickets/`](http://localhost:8000/api/helpdesk/tickets/) | Tickets que puedo ver, lo más nuevo arriba. Filtros: `?scope=mine|assigned|queue` (los que levanté / asignados a mí / de los departamentos que atiendo), `?status=open,in_progress` (uno o varios), `?priority=`, `?department=<id>`, `?unassigned=1`, `?q=<texto o folio HD-00042>`. |
| POST | `/api/helpdesk/tickets/` | Levantar (multipart): `category`, `title`, `description`, `files` (hasta 5). Responde el ticket completo (201). |
| GET | `/api/helpdesk/tickets/<id>/` | Ticket completo: `description`, `attachments`, `comments` (con sus archivos), `events` (historial) y `permissions` (qué botones mostrar). |
| PATCH | `/api/helpdesk/tickets/<id>/` | Agentes: `status`, `priority`, `assignee` (id o `null`), `category` (transferir). Quien lo levantó: solo `{"status": "closed"}` (cerrar) o `{"status": "open"}` (reabrir uno resuelto). Si al transferirlo dejas de verlo, responde la forma corta con `"visible": false`. |
| POST | `/api/helpdesk/tickets/<id>/comments/` | Responder (multipart): `body`, `is_internal` (nota interna, solo agentes), `files` (hasta 5). Hace falta `body` o algún archivo. Responde el ticket completo (201). |
| GET | `/api/helpdesk/tickets/<id>/agents/` | A quién se le puede asignar (solo agentes del departamento). |
| GET | `/api/helpdesk/attachments/<id>/file/` | Descargar un archivo (si ves el ticket; los de notas internas, solo agentes). Imágenes en línea, lo demás como descarga con su nombre original. |

- **Estados:** `open` (Abierto) → `in_progress` (En proceso) → `waiting` (En espera) → `resolved` (Resuelto) → `closed` (Cerrado, final: ya no se comenta ni se cambia). Quien pone un ticket sin responsable «En proceso» lo toma. Si quien lo levantó responde mientras está «En espera», vuelve a «En proceso».
- **Prioridad:** `low`, `normal` (por omisión), `high`, `urgent`. Solo la cambian los agentes.
- **Folio:** `HD-` + id a 5 dígitos. `first_response_at`: primera respuesta pública de un agente.
- **Archivos:** PDF, Word/Excel/PowerPoint modernos sin macros, CSV, TXT e imágenes PNG/JPEG/WebP, hasta 20 MB cada uno; se valida el contenido real (`apps/core/uploads.py` → `check_document_upload`). Ejecutables, scripts, HTML, SVG, zip, `.doc`/`.xls` viejos y Office con macros se rechazan aunque se renombren.
- **Avisos** (`notify`): ticket nuevo → agentes del departamento; asignado → responsable; respuesta o cambio de estado de un agente → quien lo levantó; respuesta, cierre o reapertura de quien lo levantó → responsable (o agentes si no tiene); transferido → agentes del nuevo departamento. Enlazan a `/helpdesk/?ticket=<id>`.

### Documentos — `apps/documents/api/`

Biblioteca de documentos con **categorías**, **privacidad** por documento y **versiones**. Suben documentos
quienes tengan `documents.documents.create`; cada dueño administra los suyos y `documents.documents.manage`
administra todos. `documents.documents.view.all` permite ver todos sin administrarlos. Los tres permisos ya
existen tras `migrate`; se asignan a un rol en el admin.

| Método | Ruta | Qué hace |
|---|---|---|
| GET | [`/api/documents/me/`](http://localhost:8000/api/documents/me/) | `{"can_create", "manage_all"}`: qué puedo hacer. |
| GET | [`/api/documents/categories/`](http://localhost:8000/api/documents/categories/) | Categorías activas (sin paginar). |
| GET | [`/api/documents/documents/`](http://localhost:8000/api/documents/documents/) | Documentos que puedo ver, los actualizados más recientemente arriba, con su versión vigente. Filtros: `?scope=mine|shared` (soy dueño / compartidos conmigo), `?category=<id>`, `?q=<texto>`. |
| POST | `/api/documents/documents/` | Subir (multipart): `title`, `category`, `file`; opcionales `description`, `notes` (de la v1), `visibility` y `departments` o `users` (ids repetidos: `users=3&users=8`). Nace como **v1**. Responde el detalle (201). |
| GET | `/api/documents/documents/<id>/` | Detalle con `versions` (historial, la más nueva primero) y `can_manage`. `departments` y `shared_with` solo llegan a quien lo administra (si no, `null`). |
| PATCH | `/api/documents/documents/<id>/` | Dueño o `manage`: `title`, `description`, `category`, `visibility`, `departments`, `users`. Al cambiar la privacidad, la lista que no aplica se vacía. Si dejas de verlo, responde `{"id", "visible": false}`. |
| DELETE | `/api/documents/documents/<id>/` | Dueño o `manage`: borrado suave (204). Versiones y archivos se conservan. |
| POST | `/api/documents/documents/<id>/versions/` | Nueva versión (multipart): `file` y `notes` (qué cambió). Queda vigente con el número siguiente (201). |
| POST | `/api/documents/documents/<id>/versions/<version_id>/restore/` | Restaura una versión anterior **copiándola como versión nueva** («Restaurada de la v1»). El historial no se reescribe (201). |
| GET | `/api/documents/versions/<id>/file/` | Descargar una versión (cualquiera del historial) si ves el documento. Imágenes en línea, lo demás como descarga con su nombre original. |

- **Privacidad** (`visibility`): `public` (Toda la empresa), `departments` (personas de los departamentos elegidos; no incluye subdepartamentos) o `users` (solo las personas elegidas). El dueño siempre lo ve.
- **Archivos:** los mismos que la mesa de ayuda (PDF, Office moderno sin macros, CSV, TXT, PNG/JPEG/WebP; hasta 20 MB), validados por contenido con `check_document_upload`.

### Muro (social) — `apps/social/api/`

| Método | URL | Qué hace |
|---|---|---|
| GET | [`/api/social/posts/`](http://localhost:8000/api/social/posts/) | Feed (lo más nuevo arriba) con adjuntos y reacciones. `?author=<id>`, `?id=<id>`. |
| POST | `/api/social/posts/` | Publicar: `body`, `audience` (`company` / `followers`) y `files` (hasta 10, multipart). |
| GET / PATCH / DELETE | `/api/social/posts/<id>/` | Ver / editar `{"body", "audience"}` / borrar (solo el autor). |
| PUT / DELETE | `/api/social/posts/<id>/reaction/` | Mi reacción. |
| GET | `/api/social/posts/<id>/reactions/` | Quién reaccionó («Ver todo»). |
| GET / POST | `/api/social/posts/<id>/comments/` | Hilos de comentarios / comentar `{"body", "parent"?}`. |
| PATCH / DELETE | `/api/social/comments/<id>/` | Editar / borrar mi comentario. |
| PUT / DELETE | `/api/social/comments/<id>/reaction/` | Mi reacción a un comentario. |
| GET | `/api/social/attachments/<id>/file/` | Archivo de un adjunto (si ves su publicación). |
| GET | `/api/social/photos/?author=<id>` | Fotos de las publicaciones de una persona (perfil → «Fotos»). |
| PUT / DELETE | `/api/social/follows/<id>/` | Seguir / dejar de seguir a una persona. |
| GET | [`/api/social/follows/suggestions/`](http://localhost:8000/api/social/follows/suggestions/) | Hasta 5 personas sugeridas para seguir. |
| GET | `/api/social/users/<id>/followers/` | Seguidores de una persona. |
| GET | `/api/social/users/<id>/following/` | A quién sigue una persona. |

### Blog — `apps/blog/api/`

Cualquiera con sesión lee los artículos **publicados**. Escribir requiere el permiso de negocio
`blog.articles.create` (en el admin: crea el permiso de negocio con ese código si no existe y asígnalo a un rol; un superusuario ya lo tiene). Solo el autor
edita o borra, y solo el autor ve sus borradores y programados.

| Método | URL | Qué hace |
|---|---|---|
| GET | [`/api/blog/articles/`](http://localhost:8000/api/blog/articles/) | Artículos publicados (tarjetas, sin `body`). Filtros: `?category=<slug>`, `?author=<id>`, `?slug=<slug>`, `?q=<texto>`, `?mine=1` (los míos en cualquier estado). |
| POST | `/api/blog/articles/` | Crear: `title`, `body` (HTML; se limpia al guardar), `excerpt`, `category`, `status` (`draft` / `published`), `published_at` (futura = programado), `cover` (WebP, multipart). |
| GET / PATCH / DELETE | `/api/blog/articles/<id>/` | Ver completo (con `body`) / editar los campos que mandes (`remove_cover: true` quita la portada) / borrar. |
| GET | `/api/blog/articles/<id>/cover/` | Portada del artículo. |
| PUT / DELETE | `/api/blog/articles/<id>/reaction/` | Mi reacción (solo en publicados). |
| GET | `/api/blog/articles/<id>/reactions/` | Quién reaccionó. |
| GET / POST | `/api/blog/articles/<id>/comments/` | Hilos / comentar `{"body", "parent"?}` (solo en publicados). |
| PATCH / DELETE | `/api/blog/comments/<id>/` | Editar / borrar mi comentario. |
| GET | [`/api/blog/categories/`](http://localhost:8000/api/blog/categories/) | Categorías activas (chips de filtro). |
| GET | [`/api/blog/permissions/`](http://localhost:8000/api/blog/permissions/) | `{"can_write"}`: si puedo escribir artículos (para mostrar el botón). |

### Marketplace — `apps/marketplace/api/`

Toda la empresa ve los artículos; solo quien publicó edita, marca como vendido o borra.

| Método | URL | Qué hace |
|---|---|---|
| GET | [`/api/marketplace/listings/`](http://localhost:8000/api/marketplace/listings/) | Artículos en venta, lo más nuevo arriba. Filtros: `?status=available|sold`, `?category=<slug>`, `?seller=<id>`, `?q=<texto>`. |
| POST | `/api/marketplace/listings/` | Publicar (multipart): `title`, `description`, `price` (vacío = «A tratar»), `category`, `files` (hasta 10 fotos WebP). |
| GET / PATCH / DELETE | `/api/marketplace/listings/<id>/` | Ver / editar los campos que mandes, incluido `{"status": "sold"}` / borrar. |
| GET | `/api/marketplace/images/<id>/file/` | Una foto de un artículo. |
| GET | [`/api/marketplace/categories/`](http://localhost:8000/api/marketplace/categories/) | Categorías activas (sin paginar). |

### Notificaciones — `apps/notifications/api/`

Cada quien ve y maneja solo las suyas; las ajenas responden 404.

| Método | URL | Qué hace |
|---|---|---|
| GET | [`/api/notifications/`](http://localhost:8000/api/notifications/) | Mis notificaciones, más recientes primero (paginado). `?unread=1`: solo las no leídas. |
| GET | `/api/notifications/<id>/` | Una notificación. |
| PATCH | `/api/notifications/<id>/` | `{"is_read": true}` marcar leída / `false` volver a no leída. |
| DELETE | `/api/notifications/<id>/` | Eliminarla. |
| GET | [`/api/notifications/unread-count/`](http://localhost:8000/api/notifications/unread-count/) | `{"unread"}`: cuántas no he leído (globito de la campana). |
| POST | `/api/notifications/read-all/` | Marcar todas como leídas. Responde `{"updated", "unread"}`. |

**Push (PWA)** — un registro por dispositivo o navegador donde la persona aceptó notificaciones:

| Método | URL | Qué hace |
|---|---|---|
| GET | [`/api/notifications/push/config/`](http://localhost:8000/api/notifications/push/config/) | `{"enabled", "public_key"}`: llave pública VAPID para `PushManager.subscribe()`. `enabled: false` si falta `WEBPUSH_VAPID_PUBLIC_KEY` en `.env`. |
| GET | [`/api/notifications/push/subscriptions/`](http://localhost:8000/api/notifications/push/subscriptions/) | Mis dispositivos (paginado; nunca devuelve las llaves). |
| POST | `/api/notifications/push/subscriptions/` | Registrar este dispositivo con lo que da `subscription.toJSON()`: `{"endpoint", "keys": {"p256dh", "auth"}}`. Si el endpoint ya existe se actualiza (y pasa a la cuenta con sesión). |
| DELETE | `/api/notifications/push/subscriptions/<id>/` | Quitar uno de mis dispositivos. |
| POST | `/api/notifications/push/unsubscribe/` | `{"endpoint"}`: quitar este navegador (lo usa el service worker, que conoce el endpoint, no el id). |

Crear notificaciones desde otras apps: `apps.notifications.services.notifications.notify(recipient=…, title=…, body=…, icon=…, color=…, url=…)`.
Hoy la llama la mesa de ayuda; las demás apps todavía no, y **el envío de push no está implementado** (falta la llave privada VAPID y la librería de envío): ver `docs/backlog.md`.

## 4. Probar desde la consola del navegador

Con la app abierta y la sesión iniciada (F12 → Consola):

```js
// Leer
fetch("/api/blog/articles/").then(r => r.json()).then(console.log);

// Escribir: necesita el token CSRF de la cookie
const csrf = document.cookie.match(/csrftoken=([^;]+)/)[1];
fetch("/api/social/posts/1/reaction/", {
  method: "PUT",
  headers: {"Content-Type": "application/json", "X-CSRFToken": csrf},
  body: JSON.stringify({emoji: "clap"}),
}).then(r => r.json()).then(console.log);
```

Las pruebas automáticas de cada API están en `tests/` (`test_social.py`, `test_blog_api.py`,
`test_marketplace.py`…) y sirven como ejemplos de uso.
