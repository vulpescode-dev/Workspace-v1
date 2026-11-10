# Roles y permisos

Todo lo que una persona puede hacer en Workspace pasa por **roles de negocio**, incluso lo que «todos
tienen» (publicar, vender, levantar tickets). Son independientes de los permisos y grupos de Django, que solo
gobiernan el `/admin/`.

```text
Usuario ──< UserRole >── Rol ──< RolePermission >── Permiso (app.recurso.acción[.all])
```

- Una persona puede tener **varios roles**; sus permisos se suman.
- **`is_superuser` pasa directo:** no se revisan sus roles (`has_permission` responde que sí a todo).
- El servidor siempre valida. El frontend solo oculta lo que no puedes usar; ocultar no es seguridad.

## Formato de los permisos

`app.recurso.acción`, y `.all` al final cuando aplica a registros **de otras personas**:

| Código | Significa |
|---|---|
| `social.posts.create` | Publicar. |
| `social.posts.delete` | Eliminar **mis** publicaciones. |
| `social.posts.delete.all` | Eliminar publicaciones **de otros** (moderación). |
| `documents.documents.view.all` | Ver todos los documentos aunque no se compartan conmigo (solo lectura). |

Acciones base: `view`, `create`, `update`, `delete`. Especiales donde aplican: `assign`, `attend`, `export`,
`import`, `print`, `download`, `pin`, `send`, `manage`.

## Dónde viven

| Archivo | Qué es |
|---|---|
| `backend/apps/accounts/data/permissions.json` | **Catálogo** de todos los permisos (app → recurso → acción → descripción). Única fuente. Los marcados ★ ya los usa el código: no cambiar su código. |
| `backend/apps/accounts/data/roles.json` | **Roles semilla** (los básicos de partida). |
| `apps/accounts/services/permissions.py` | `has_permission`, `require_permission`, `user_permission_codenames`. |
| `apps/accounts/api/permissions.py` | Acceso por sección para las vistas (`SOCIAL_POSTS`, `MARKETPLACE`…). |
| `apps/accounts/services/roles.py` | Roles por defecto y «asignar a todos». |
| `frontend/src/features/accounts/access.ts` | Qué permisos abren cada sección (mismo criterio que el backend) y la regla `hasPermission`. |
| `frontend/src/features/accounts/hooks/useCan.ts` | `useCan()` y `useSectionAccess()`. |

### Carga

- En cada `migrate` se **crean y actualizan** los permisos del catálogo y se **crean** los roles semilla que no
  existan (los existentes no se tocan: lo que cambies en el admin se respeta).
- A mano:

  ```bash
  .venv/Scripts/python manage.py load_permissions           # crea/actualiza
  .venv/Scripts/python manage.py load_permissions --prune   # además borra los que ya no estén en el catálogo
  .venv/Scripts/python manage.py load_roles                 # crea los roles semilla que falten
  .venv/Scripts/python manage.py load_roles --update        # los deja exactamente como en roles.json
  ```

- En el admin, los permisos son de **solo lectura** (salen del catálogo) y se filtran por app. Se asignan a roles
  desde cada rol.

## Roles semilla

| Rol | Por defecto | Qué da |
|---|---|---|
| **Lector** | Sí | Ver lo básico: publicaciones, estados, noticias, documentos compartidos (y descargarlos), formularios, sus tickets, anuncios, directorio, departamentos y organigrama. Sin `.all`. |
| **Influencer** | Sí | Casi todo el Inicio: publicar y subir estados (editar/borrar los propios), comentar (también en noticias), reaccionar y seguir. |
| **Vendedor** | Sí | Publicar anuncios en el Marketplace. |
| **Solicitante de soporte** | Sí | Levantar tickets en la Mesa de ayuda. |
| **Blogger** | No | Escribir y publicar noticias. |

### Roles por defecto (`Role.is_default`)

- Cada usuario **nuevo** recibe los roles activos marcados así, venga de donde venga (admin, Google,
  `createsuperuser`, scripts): lo hace una señal `post_save` (`apps/accounts/signals.py`).
- A quien ya existe **no** se le agregan solos. En el admin → Roles → acción **«Asignar a todos los usuarios
  activos»** (solo a quien le falte).
- Se le pueden quitar a una persona en particular desde su ficha.

## Qué exige permiso

### Entrar a cada sección (`view`)

Entra quien tenga el `view` de la sección **o** un permiso que ya implique verla (crear, atender, administrar,
`.view.all`). Sin acceso, la API responde **403** y el frontend no muestra la sección en el menú; si se entra por
URL, aparece «No tienes acceso a esta sección» (`RequireAccess`).

| Sección | Permisos que la abren |
|---|---|
| Personas, Calendario, cumpleaños | `accounts.users.view`, `accounts.users.view.all` |
| Organigrama | `org.chart.view` |
| Departamentos | `org.departments.view` |
| Publicaciones (feed, comentarios, reacciones) | `social.posts.view`, `.view.all`, `social.posts.create` |
| Estados | `social.stories.view`, `social.stories.create` |
| Noticias | `blog.articles.view`, `.view.all`, `blog.articles.create` |
| Documentos | `documents.documents.view`, `.view.all`, `.create`, `.manage` |
| Formularios | `forms.forms.view`, `.view.all`, `.create` |
| Mesa de ayuda | `helpdesk.tickets.view`, `.view.all`, `.create`, `.attend` |
| Marketplace | `marketplace.listings.view`, `.create` |

Siempre abiertos: mi perfil (`/api/accounts/me/`), mis avisos y las fotos de perfil.

### Acciones

| Acción | Permiso |
|---|---|
| Publicar / editar / borrar mis publicaciones | `social.posts.create` / `.update` / `.delete` |
| Comentar / editar / borrar mis comentarios (Inicio) | `social.comments.create` / `.update` / `.delete` |
| Comentar / editar / borrar mis comentarios (Noticias) | `blog.comments.create` / `.update` / `.delete` |
| Reaccionar (posts, comentarios, noticias) | `social.reactions.create` (quitar mi reacción no lo pide) |
| Subir / borrar mis estados | `social.stories.create` / `.delete` |
| Seguir | `social.follows.create` (dejar de seguir no lo pide) |
| Escribir noticias | `blog.articles.create` |
| Subir documentos / administrarlos todos | `documents.documents.create` / `.manage` |
| Descargar documentos | `documents.documents.download` (quien administra el documento, siempre) |
| Crear formularios | `forms.forms.create` |
| Ver resultados de formularios ajenos | `forms.forms.view.all` o `forms.submissions.view.all` (los propios, siempre) |
| CSV de formularios ajenos | Lo anterior + `forms.submissions.export` (los propios, siempre) |
| Publicar anuncios | `marketplace.listings.create` |
| Levantar tickets | `helpdesk.tickets.create` |
| Atender tickets de su departamento | `helpdesk.tickets.attend` (tomarlo uno mismo incluido) |
| Asignar un ticket a otra persona | `helpdesk.tickets.assign` |

### Moderación (lo ajeno)

| Contenido | Editar | Eliminar |
|---|---|---|
| Publicaciones, comentarios, estados | — | `social.posts.delete.all`, `social.comments.delete.all`, `social.stories.delete.all` |
| Comentarios de noticias | — | `blog.comments.delete.all` |
| Noticias | `blog.articles.update.all` | `blog.articles.delete.all` |
| Anuncios | `marketplace.listings.update.all` | `marketplace.listings.delete.all` |
| Formularios | `forms.forms.update.all` | `forms.forms.delete.all` |

Ningún rol semilla los trae: se crea un rol (p. ej. «Moderación») y se asigna a quien modere.

### En el catálogo pero sin uso todavía

Quedan listos para cuando exista la función: fijar publicaciones, imprimir, exportar/importar, avisos a toda la
empresa, y administrar usuarios, roles, departamentos, categorías y emojis desde React (hoy se hace en el admin
de Django con sus propios permisos).

## En el frontend

`GET /api/accounts/me/` trae, solo en tu propio perfil:

```json
"access": { "is_superuser": false, "permissions": ["social.posts.create", "..."] }
```

```tsx
const can = useCan()
{can('social.posts.create') && <PostComposer />}

const { ready, canSee } = useSectionAccess()
canSee('marketplace')   // ¿abre la sección?
```

- `useCan` responde `false` mientras `/me` carga (mejor no mostrar un botón que luego desaparece).
- `useSectionAccess().canSee` responde `true` mientras carga (el menú no parpadea); `RequireAccess` espera a
  `ready` antes de decidir.
- Si a alguien le quitan un rol con la sesión abierta, los botones se actualizan al recargar; mientras tanto el
  servidor rechaza la acción con 403 y la app lo avisa.

## Agregar un permiso nuevo

1. Agregarlo a `permissions.json` (con descripción).
2. Exigirlo en el servicio: `require_permission(user, "app.recurso.accion", "Mensaje")`, o en la vista con
   `section(...)` si abre una sección.
3. Si lo debe tener todo el mundo, agregarlo a un rol semilla en `roles.json` (y `load_roles --update`).
4. En React: `useCan()('app.recurso.accion')` para mostrar u ocultar el botón; si es una sección, en
   `features/accounts/access.ts`.
5. Pruebas en `backend/tests/` (sin el permiso → 403; con él → permitido).
