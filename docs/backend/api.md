# API del backend

Todas las APIs del proyecto en un solo lugar: qué hay, cómo verlas en el navegador y cómo llamarlas.
Si agregas o cambias un endpoint, **actualiza este archivo** (y la raíz `/api/` en `config/api.py`).

## 1. Cómo verlas en el navegador

1. Levanta el servidor: `cd backend` y `.venv/Scripts/python manage.py runserver`.
2. Inicia sesión en **<http://localhost:8000/admin/>** con una cuenta de personal (`is_staff`): la
   interfaz navegable usa esa sesión. React no usa sesión, usa JWT (ver `autenticacion.md`).
3. Entra a **<http://localhost:8000/api/>**: es la raíz, con enlaces a cada sección. Desde ahí, o
   escribiendo cualquier URL de las tablas de abajo, Django REST Framework muestra la **interfaz
   navegable**: el JSON con formato, los métodos permitidos y, abajo, un formulario para probar
   `POST` / `PUT` / `PATCH` / `DELETE`.

Notas:

- La interfaz navegable solo existe en **desarrollo** (`config/settings/development.py`). En producción
  la API responde únicamente JSON.
- Sin token (ni sesión de admin), todo responde **401** (excepto la raíz `/api/`, `/api/health/` y `/api/auth/`).
- Para ver solo el JSON agrega `?format=json` (p. ej. <http://localhost:8000/api/social/posts/?format=json>).
- Lista completa de rutas desde la terminal (django-extensions):

  ```bash
  python manage.py show_urls
  ```

## 2. Reglas comunes

| Tema | Regla |
|---|---|
| Raíz | Única base `/api/`, **sin versión** (nada de `/api/v1/`). |
| Autenticación | **JWT**: `Authorization: Bearer <access>` (lo pone `frontend/src/lib/api/client.ts`). Login, refresh y logout en `/api/auth/` (detalle en `autenticacion.md`). La sesión de Django solo sirve para la interfaz navegable tras entrar al admin. |
| CSRF | Con JWT no aplica. Solo si se usa la sesión del admin, lo que no sea `GET` necesita `X-CSRFToken`. |
| Paginación | Todas las listas: `?page=<n>` y `?page_size=<n>` (**25 por omisión y máximo 25**; más de 25 se limita a 25, un valor inválido usa 25). Respuesta: `{"count", "page", "total_pages", "next", "previous", "results"}`. Una página inexistente responde 404 con `count` y `total_pages`. Solo los catálogos cortos (emojis, categorías) no se paginan. |
| Errores | `400` con `{"campo": ["mensaje"]}`; `403` sin permiso (p. ej. editar algo ajeno); `404` si no existe, está eliminado o no lo puedes ver. |
| Permisos | Todo pasa por roles de negocio (ver [`permisos.md`](permisos.md)): cada sección exige su `view` (o algo que lo implique) y cada acción su permiso; sin él, `403` con `{"detail": "…"}`. El superusuario pasa directo. |
| Archivos | Fotos y videos nunca salen de `/media/`: cada uno tiene su endpoint `…/file/` o `…/cover/` que revisa si lo puedes ver. Se suben en **multipart**; imágenes solo **WebP** (el navegador convierte antes de subir, ver `media-uploads.md`). |
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

### Autenticación (JWT) — `apps/accounts/api/auth.py`

| Método | URL | Qué hace |
|---|---|---|
| POST | `/api/auth/login/` | `{"username", "password"}` (usuario **o** correo). 200 `{"access"}` + cookie httpOnly con el refresh. 401 genérico «Usuario o contraseña incorrectos.» (no revela si la cuenta existe o está desactivada). 429 tras 10 intentos por minuto por IP (`AUTH_THROTTLE_RATE`). |
| POST | `/api/auth/refresh/` | Sin cuerpo: usa la cookie. 200 `{"access"}` y rota la cookie (el refresh anterior queda revocado). 401 si no hay cookie o ya no sirve (la borra). |
| POST | `/api/auth/logout/` | Revoca el refresh de la cookie y la borra. Siempre 204. |

### Cuentas — `apps/accounts/api/`

| Método | URL | Qué hace |
|---|---|---|
| GET | [`/api/accounts/me/`](http://localhost:8000/api/accounts/me/) | Mi perfil. Incluye `department` (nombre), `department_id`, `manager` (jefe directo en forma corta, o `null`) y `access`: `{"is_superuser", "permissions": ["app.recurso.acción", …]}` (solo en mi perfil, nunca en el de otra persona; también en las respuestas de PATCH y de la foto). |
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

### Organización — `apps/accounts/api/org_*.py` (modelo `accounts.Department`)

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

Las categorías son la **lista de problemas** («Acceso a ERP» → Sistemas): el sistema ya sabe a qué
departamento mandarlo. Si el problema no está en la lista, se levanta como **«Otro»** (sin `category`):
queda **sin clasificar** (`category` y `department` = `null`), lo ven y atienden los agentes de *todos*
los departamentos, y el que sepa de qué trata le pone categoría (PATCH `category`) y pasa a ese departamento.

| Método | URL | Qué hace |
|---|---|---|
| GET | [`/api/helpdesk/me/`](http://localhost:8000/api/helpdesk/me/) | `{"attends": [{id, name}], "all_departments", "view_all"}`: qué departamentos atiendo. |
| GET | [`/api/helpdesk/categories/`](http://localhost:8000/api/helpdesk/categories/) | Categorías que se pueden elegir (sin paginar), con su departamento y `kind` (`incident` / `request`). `?department=<id>`. |
| GET | [`/api/helpdesk/tickets/`](http://localhost:8000/api/helpdesk/tickets/) | Tickets que puedo ver, lo más nuevo arriba. Filtros: `?scope=mine|assigned|queue` (los que levanté / asignados a mí / de los departamentos que atiendo, más los sin clasificar), `?status=open,in_progress` (uno o varios), `?priority=`, `?department=<id>`, `?unassigned=1`, `?unclassified=1` (solo «Otro» sin clasificar), `?q=<texto o folio HD-00042>`. |
| POST | `/api/helpdesk/tickets/` | Levantar (multipart): `category` (omitido o vacío = «Otro»), `title`, `description`, `files` (hasta 5). Responde el ticket completo (201). |
| GET | `/api/helpdesk/tickets/<id>/` | Ticket completo: `description`, `attachments`, `comments` (con sus archivos), `events` (historial) y `permissions` (qué botones mostrar). |
| PATCH | `/api/helpdesk/tickets/<id>/` | Agentes: `status`, `priority`, `assignee` (id o `null`; tomarlo uno mismo basta con ser agente, dárselo a otra persona pide `helpdesk.tickets.assign`), `category` (transferir, o clasificar uno «Otro»). Quien lo levantó: solo `{"status": "closed"}` (cerrar) o `{"status": "open"}` (reabrir uno resuelto). Si al transferirlo dejas de verlo, responde la forma corta con `"visible": false`. |
| POST | `/api/helpdesk/tickets/<id>/comments/` | Responder (multipart): `body`, `is_internal` (nota interna, solo agentes), `files` (hasta 5). Hace falta `body` o algún archivo. Responde el ticket completo (201). |
| GET | `/api/helpdesk/tickets/<id>/agents/` | A quién se le puede asignar (solo agentes del departamento; sin clasificar: agentes de todos). |
| GET | `/api/helpdesk/attachments/<id>/file/` | Descargar un archivo (si ves el ticket; los de notas internas, solo agentes). Imágenes en línea, lo demás como descarga con su nombre original. |

- **Estados:** `open` (Abierto) → `in_progress` (En proceso) → `waiting` (En espera) → `resolved` (Resuelto) → `closed` (Cerrado, final: ya no se comenta ni se cambia). Quien pone un ticket sin responsable «En proceso» lo toma. Si quien lo levantó responde mientras está «En espera», vuelve a «En proceso».
- **Prioridad:** `low`, `normal` (por omisión), `high`, `urgent`. Solo la cambian los agentes.
- **Folio:** `HD-` + id a 5 dígitos. `first_response_at`: primera respuesta pública de un agente.
- **Archivos:** PDF, Word/Excel/PowerPoint modernos sin macros, CSV, TXT e imágenes PNG/JPEG/WebP, hasta 20 MB cada uno; se valida el contenido real (`apps/core/uploads.py` → `check_document_upload`). Ejecutables, scripts, HTML, SVG, zip, `.doc`/`.xls` viejos y Office con macros se rechazan aunque se renombren.
- **Avisos** (`notify`): ticket nuevo → agentes del departamento (si es «Otro», agentes de todos los departamentos); asignado → responsable; respuesta o cambio de estado de un agente → quien lo levantó; respuesta, cierre o reapertura de quien lo levantó → responsable (o agentes si no tiene); transferido o clasificado → agentes del nuevo departamento. Enlazan a `/helpdesk/?ticket=<id>`.

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
| GET | `/api/documents/versions/<id>/file/` | Descargar una versión (cualquiera del historial) si ves el documento y tienes `documents.documents.download` (quien lo administra, siempre). Imágenes en línea, lo demás como descarga con su nombre original. |

- **Privacidad** (`visibility`): `public` (Toda la empresa), `departments` (personas de los departamentos elegidos; no incluye subdepartamentos) o `users` (solo las personas elegidas). El dueño siempre lo ve.
- **Archivos:** los mismos que la mesa de ayuda (PDF, Office moderno sin macros, CSV, TXT, PNG/JPEG/WebP; hasta 20 MB), validados por contenido con `check_document_upload`.

### Formularios — `apps/form_builder/api/`

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/forms/me/` | `{"can_create"}`: si puedo crear formularios. |
| GET / POST | `/api/forms/forms/` | Lista: `?scope=pending` (abiertos sin responder), `?scope=mine` (los míos, con borradores) o todos los publicados; `?q=` busca en el título. POST `{"title", "description"?}` (`forms.forms.create`): crea un borrador. |
| GET / PATCH / DELETE | `/api/forms/forms/<uuid>/` | Ver con sus preguntas / editar título, descripción, estado (`draft`/`open`/`closed`), `opens_at`, `closes_at`, `one_submission_per_user` / borrar (suave). Editar y borrar: quien lo creó, o con `forms.forms.update.all` / `.delete.all`. |
| PUT | `/api/forms/forms/<uuid>/questions/` | `{"questions": [...]}`: guarda la lista completa de preguntas, en orden (mismos permisos que editar). |
| POST | `/api/forms/forms/<uuid>/submissions/` | `{"answers": [{"question", …}]}`: responder. Errores por pregunta en `{"answers": {"<id>": "mensaje"}}`. |
| GET | `/api/forms/forms/<uuid>/results/` | Resumen por pregunta para las gráficas. Quien lo creó, o con `forms.forms.view.all` / `forms.submissions.view.all`. |
| GET | `/api/forms/forms/<uuid>/results.csv` | Todas las respuestas en CSV (UTF-8 con BOM). Quien lo creó, siempre; otra persona, si ve los resultados y tiene `forms.submissions.export`. |

### Muro (social) — `apps/social/api/`

| Método | URL | Qué hace |
|---|---|---|
| GET | [`/api/social/posts/`](http://localhost:8000/api/social/posts/) | Feed (lo más nuevo arriba) con adjuntos y reacciones. `?author=<id>`, `?id=<id>`. |
| POST | `/api/social/posts/` | Publicar: `body`, `audience` (`company` / `followers`) y `files` (hasta 10, multipart). |
| GET / PATCH / DELETE | `/api/social/posts/<id>/` | Ver / editar `{"body", "audience"}` (el autor, con `social.posts.update`) / borrar (el autor con `social.posts.delete`; otra persona con `social.posts.delete.all`). |
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

#### Estados (tipo Instagram) — `apps/social/api/` (`StoryListCreateView`…)

Foto o video que se ve **24 horas**. Visibles para **toda la empresa** (por decidir si también «solo seguidores»).
Máximo 20 estados activos por persona. Mismo validador que los adjuntos (`check_media_upload`).

| Método | URL | Qué hace |
|---|---|---|
| GET | `/api/social/stories/` | Fila de Inicio, sin paginar: `[{"author", "is_mine", "has_unseen", "latest_at", "stories": [{"id", "kind", "url", "content_type", "width", "height", "created_at", "expires_at", "seen"}]}]`. Orden: los míos, luego con estados sin ver, luego vistos; dentro de cada bloque, el más reciente primero. Solo estados vivos (no vencidos ni eliminados) de personas activas. |
| POST | `/api/social/stories/` | Multipart `file` (imagen **WebP** o video MP4/MOV/WebM). 201 con el estado. 400 `{"file": "…"}` si no es válido o ya hay 20 activos. |
| DELETE | `/api/social/stories/<id>/` | Elimina un estado (borrado suave): el mío con `social.stories.delete`; uno ajeno solo con `social.stories.delete.all`. |
| POST | `/api/social/stories/<id>/seen/` | Lo marca como visto por mí (una vez; los propios no cuentan). 204. |
| GET | `/api/social/stories/<id>/viewers/` | «Visto por» de **mi** estado, paginado: `[{"user", "viewed_at"}]`. De un estado ajeno: 403. En la fila, `views_count` solo llega en mis estados (en los ajenos es `null`). |
| GET | `/api/social/stories/<id>/file/` | Archivo del estado (vivo). Vencido o eliminado: 404. |

### Blog — `apps/blog/api/`

Cualquiera con sesión lee los artículos **publicados**. Escribir requiere el permiso de negocio
`blog.articles.create` (en el admin: crea el permiso de negocio con ese código si no existe y asígnalo a un rol; un superusuario ya lo tiene). Solo el autor
edita o borra, y solo el autor ve sus borradores y programados.

| Método | URL | Qué hace |
|---|---|---|
| GET | [`/api/blog/articles/`](http://localhost:8000/api/blog/articles/) | Artículos publicados (tarjetas, sin `body`). Filtros: `?category=<slug>`, `?author=<id>`, `?slug=<slug>`, `?q=<texto>`, `?mine=1` (los míos en cualquier estado). |
| POST | `/api/blog/articles/` | Crear: `title`, `body` (HTML; se limpia al guardar), `excerpt`, `category`, `status` (`draft` / `published`), `published_at` (futura = programado), `cover` (WebP, multipart). |
| GET / PATCH / DELETE | `/api/blog/articles/<id>/` | Ver completo (con `body`) / editar los campos que mandes (`remove_cover: true` quita la portada) / borrar. Quien la escribió, o con `blog.articles.update.all` / `.delete.all`. |
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
| GET / PATCH / DELETE | `/api/marketplace/listings/<id>/` | Ver / editar los campos que mandes, incluido `{"status": "sold"}` / borrar. Quien lo publicó, o con `marketplace.listings.update.all` / `.delete.all`. |
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

Crear notificaciones desde otras apps: `apps.notifications.services.notifications.notify(recipient=…, title=…, body=…, icon=…, color=…, url=…, key=…)`.
Con `key` (clave del evento) repetir el mismo evento **actualiza** el aviso (no duplica ni vuelve a avisar) y
`withdraw(key=…)` / `withdraw(prefix=…)` lo retira si la acción se deshace o el objeto se elimina.

Quién genera avisos hoy:

| Evento | Recibe | Título | Lleva a | Se retira al… |
|---|---|---|---|---|
| Reacción a una publicación | autor del post | «X reaccionó a tu publicación» (emoji + extracto) | `/posts/<id>/` | quitar la reacción o eliminar el post |
| Comentario | autor del post | «X comentó tu publicación» | `/posts/<id>/?comments=1` | eliminar el comentario o el post |
| Respuesta | autor del comentario respondido (y el del post) | «X respondió a tu comentario» | `/posts/<id>/?comments=1` | eliminar la respuesta o el post |
| Reacción a un comentario | autor del comentario | «X reaccionó a tu comentario» | `/posts/<id>/?comments=1` | quitar la reacción, eliminar el comentario o el post |
| Seguir | persona seguida | «X empezó a seguirte» | `/profile/<id>` | dejar de seguir |
| Mesa de ayuda | solicitante / agentes | ticket nuevo, asignado, respuesta, estado… | `/helpdesk/?ticket=<id>` | — |

Nadie recibe avisos de sus propias acciones; cambiar de emoji actualiza el aviso; editar un comentario
actualiza su texto. Reglas en `apps/social/services/notifications.py`. **El envío de push no está
implementado** (falta la llave privada VAPID y la librería de envío): ver `docs/checklist.md`.

## 4. Probar con JWT desde la terminal

```bash
# 1) Login: el access llega en el cuerpo; el refresh queda en la cookie (cookies.txt)
curl -s -c cookies.txt -H "Content-Type: application/json"   -d '{"username": "bot.ana", "password": "1234"}' http://localhost:8000/api/auth/login/

# 2) Usar el access en cualquier endpoint
curl -s -H "Authorization: Bearer <access>" http://localhost:8000/api/accounts/me/

# 3) Pedir otro access con la cookie (rota la cookie)
curl -s -b cookies.txt -c cookies.txt -X POST http://localhost:8000/api/auth/refresh/
```

Las pruebas automáticas de cada API están en `backend/tests/api/` (`test_social.py`, `test_blog_api.py`,
`test_marketplace.py`…) y sirven como ejemplos de uso.
