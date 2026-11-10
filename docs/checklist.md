# Checklist del proyecto

Lista viva. Se trabaja **por tandas**: al cerrar una tanda se marca aquí lo hecho y se ajusta lo pendiente.
Cuando se pregunte «¿qué falta?», la respuesta sale de este archivo.

Estados: `[x]` hecho · `[~]` en curso o parcial · `[ ]` pendiente · **(decidir)** necesita decisión del responsable.

---

## Estado por módulo

«Backend» = modelos + servicios + API probados. «Frontend» = pantalla en React.

| Módulo | Backend | Frontend | Requisitos |
|---|---|---|---|
| Acceso (login/logout JWT) | [x] | [x] Login | RF-ACC-01…04 |
| Google | [~] reglas de dominio listas; falta canje por JWT | [ ] botón «Próximamente» | RF-ACC-05 |
| Roles y permisos | [x] catálogo de 88 permisos (`accounts/data/permissions.json`), roles básicos (`roles.json`: Lector, Influencer, Vendedor y Solicitante de soporte por defecto; Blogger), roles por defecto `is_default`; `/me` → `access` + `useCan()`; todo pasa por permisos: crear (posts, comentarios, reacciones, estados, seguir, anuncios, tickets), editar/eliminar lo propio, moderar con `.delete.all` y entrar a cada sección (`view`): API 403 + menú, rutas (`RequireAccess`) y botones | — (admin) | RF-ACC-07 |
| Inicio | — | [x] estados, publicar, feed y widgets | RF-HOME-01…03 |
| Social (posts, comentarios, reacciones, adjuntos, seguir) | [x] | [x] feed, publicar, editar/borrar, reacciones animadas, comentarios, galería | RF-SOC-01…05 |
| Estados (tipo Instagram) | [x] | [x] fila con aros, subir, visor y «Visto por» | RF-SOC-06 |
| Avisos / notificaciones | [x] API; [ ] envío push | [x] página, campana y contador | RF-NOT-01…03 |
| Directorio y perfil | [x] | [x] perfil (4 pestañas, editar), directorio con búsqueda y área | RF-ORG-01…02 |
| Departamentos y organigrama | [x] | [x] organigrama (d3-org-chart) | RF-ORG-03 |
| Documentos | [x] | [x] lista, subir, detalle con versiones, editar ficha y compartir con personas | RF-DOC-01…02 |
| Formularios | [x] | [x] por responder, responder (11 tipos), editor, resultados con gráficas y CSV | RF-FRM-01…02 |
| Mesa de ayuda | [x] | [x] cola por departamento, levantar ticket con adjuntos, conversación con notas internas e historial, atender | RF-HD-01…02 |
| Noticias (blog) | [x] | [x] lista, detalle con reacciones y comentarios, escribir/editar con Tiptap | RF-BLOG-01 |
| Marketplace | [x] | [x] lista con filtros, detalle con galería, publicar/editar con fotos, vendido | RF-MKT-01 |
| Catálogo de emojis | [x] | [x] hoja animada (Lottie), pastillas y «Ver todo» | RF-SOC-03 |
| Calendario | [ ] | [~] solo visual: cuadrícula del mes con cumpleaños (próximos 30 días) | RF-CAL-01 |
| Búsqueda general | [x] usa las APIs de cada sección (+ `?q=` en publicaciones) | [x] `/search` por secciones | RF-SRCH-01 |
| Correo | [~] preparado, falta cuenta `no-reply@` | — | RF-MAIL-01 |
| Permisos y vacaciones | [ ] **(decidir)** | [ ] | RF-LEAVE-01 |
| Pantallas de error | — | [x] 404, 500 (error de pantalla) y sin conexión, con emojis animados; vista previa en `/dev/errors/*` solo en desarrollo | — |
| PWA | [~] push: tabla y API | [ ] manifest, service worker, instalar | RF-NOT-03 |

---

## Tanda 0 — Reestructuración (hecha, noviembre 2026)

- [x] Proyecto dividido en `backend/` y `frontend/`; raíz solo con `backend`, `frontend`, `docs`, `.vscode` (+ `README.md`, `AGENT.md`).
- [x] Sin rastro de git (se reconstruirá el repositorio).
- [x] Backend solo API + admin: se quitaron plantillas, vistas HTML, Bootstrap, jQuery y `showcase.html`. Se conservan `templates/emails/` y los emojis del catálogo.
- [x] `.env` completo: `PROJECT_NAME`, `PROJECT_CODE`, `DJANGO_ENV`, hosts, `FRONTEND_URL`, CORS/CSRF, base de datos, JWT, correo, Google. `manage.py`/`wsgi`/`asgi` eligen ajustes con `DJANGO_ENV`.
- [x] **JWT activo:** `/api/auth/login|refresh|logout/`, refresh en cookie httpOnly con rotación y lista negra, límite de intentos.
- [x] Pruebas por tipo (`auth`, `google`, `api`, `database`, `uploads`, `mail`, `core`) — 243 pasan.
- [x] Frontend React + TypeScript + Vite + Tailwind v4, arquitectura por features, TanStack Query, React Router.
- [x] Pantallas: Login (usuario/correo, mostrar contraseña, error genérico, Google «Próximamente») e Inicio (bienvenida). Menú de cuenta con cerrar sesión. 404.
- [x] Tipografía: Inter (interfaz) + Montserrat (títulos). Movimiento según Emil Kowalski.
- [x] Documentación nueva en `docs/`.
- [x] Fuera de alcance: cursos tipo Udemy (no había código ni documentación de eso).

---

## Fase 1 — Permisos, validaciones y errores (cerrada, noviembre 2026)

- [x] Catálogo de permisos (`accounts/data/permissions.json`) y roles semilla (`roles.json`) cargados al migrar; roles por defecto (`is_default`).
- [x] Todo pasa por permisos: entrar a cada sección, crear, editar/eliminar lo propio, moderar lo ajeno, descargar documentos, ver/exportar resultados ajenos de formularios y asignar tickets a otra persona. API 403 + menú, rutas (`RequireAccess`) y botones (`useCan`).
- [x] `/me` → `access` (`is_superuser` + permisos). El superusuario pasa directo.
- [x] Pantallas 404, 500 y sin conexión; carga diferida por ruta con errores atrapados por la raíz.
- [x] Lint solo del código (`npm run lint` → `oxlint src`), sin avisos.
- [x] Pruebas del frontend con Vitest (`npm test`): reglas de permisos y descripción de anuncios.
- [x] Migraciones consolidadas: una `0001_initial` por app (la app `org` se unió a `accounts`: `Department` y `User` se apuntan entre sí; la API sigue en `/api/org/`), con las cargas de emojis y categorías dentro. La base local se alineó sin perder datos.
- [x] Repositorio listo para git: `.gitignore` en raíz, `backend/` y `frontend/` (`.vscode/` sí se sube).
- [ ] Permisos del catálogo para funciones que aún no existen: fijar posts, imprimir, exportar/importar, avisos a toda la empresa, y administrar usuarios, roles, departamentos y categorías desde React (hoy, admin de Django).

## Próximas tandas (propuesta, en orden)

### Tanda 1 — Armazón de la app
- [x] Barra inferior en teléfono y tablet (< 1024 px): Inicio · Avisos · Buscar · Más, píldora en el destino activo, globito de avisos sin leer (consulta cada minuto), zona segura.
- [x] Hoja «Más» (Vaul): Aplicaciones en cuadrícula de 3, Cuenta, Cerrar sesión y pie legal; se cierra arrastrando.
- [x] Campana con globito en el encabezado → Avisos.
- [x] Mapa de navegación único (`app/navigation.ts`) y página «Próximamente» para lo que no tiene pantalla.
- [x] Menú lateral en escritorio (≥ 1024 px) con el mismo `navigation.ts`: Principal (con globito en Avisos) · Aplicaciones · Cuenta (con Cerrar sesión) · pie legal. Fijo al desplazar, alineado con el logo, scroll propio discreto.
- [x] Componentes base: `Sheet` (Vaul), `Menu`, `Tabs`, `Skeleton`, `CountBadge`.
- [ ] Manifest PWA e íconos (ya están en `public/icons/`).

### Tanda 2 — Social en Inicio (hecha, noviembre 2026)
- [x] **Esqueletos** con la misma forma que el contenido real: publicaciones, estados, widgets (`components/feedback/Skeleton`, `ListSkeleton`, `PostCardSkeleton`). Errores con «Reintentar» y estados vacíos honestos.
- [x] `features/posts`: `PostCard` única (Inicio, y luego Perfil/Detalle/Búsqueda), feed con scroll infinito (25 por página), «Ver más», mosaico de fotos (1/2/3/4+ con «+N»), videos que se descargan solo al tocar «reproducir».
- [x] Composer: texto, audiencia (Toda la empresa / Solo seguidores), hasta 10 fotos/videos; fotos convertidas a WebP en el navegador (`lib/media/to-webp.ts`).
- [x] `features/reactions`: pastillas compactas (tocar = poner/quitar), **hoja inferior con emojis animados (Lottie)** como el diseño anterior, animación al elegir, «Ver todo», sin reordenar pastillas; optimista con regreso si falla.
- [x] **Estados (tipo Instagram)** — backend: `Story` + `StoryView`, 24 horas, máx. 20 activos, API (`/api/social/stories/`), admin y 9 pruebas. Frontend: fila con la foto de cada persona y aro (color = sin ver o mi estado vivo, gris = visto), «Tu estado +» para subir foto o video.
- [x] Widgets (≥ 1280 px): Cumpleaños y Personas que quizás conozcas (con Seguir); se ocultan si no hay datos. «Avisos recientes» se quitó (sobraba: ya están la campana y la página Avisos). La columna tiene scroll **vertical** propio y nunca se desborda a lo ancho (los nombres largos se cortan con «…»).
- [x] Hoja de emojis a todo el ancho también en escritorio (corregido: un panel flotante no era lo pedido). Lottie completo: ya no hay emojis en blanco.
- [x] Visor de estados a pantalla completa (en pantallas anchas el marco toma la proporción de la foto/video): barras de progreso (foto 5 s, video lo que dure), tocar izquierda/derecha, mantener para pausar, teclado, pasa a la siguiente persona, marca visto y permite borrar el mío.
- [x] Comentarios en hoja inferior: hilos con respuestas de un nivel, escribir/responder, editar y eliminar los míos, reacciones con la misma hoja animada; actualiza el contador de la tarjeta.
- [x] «Visto por» en mis estados: contador abajo en el visor (solo lo ve el autor) y lista; API `/api/social/stories/<id>/viewers/`.
- [x] Editar (texto y audiencia, en la misma tarjeta) y eliminar publicaciones propias desde el menú «…».
- [x] Galería a pantalla completa: fotos y videos del post, flechas/teclado/deslizar, contador.
- [ ] Purga de estados vencidos (comando programado que borre registros y archivos).
- [ ] **(decidir)** ¿Estados visibles para toda la empresa (hoy) o solo para seguidores? ¿Respuestas a estados?
- [x] Bundle dividido por ruta (`lazy` en `router.tsx`): el principal bajó de 1 272 KB a 400 KB; ya no hay avisos de > 500 kB.

### Tanda 3 — Perfil y Personas (hecha, noviembre 2026)
- [x] **Perfil** (`/profile` y `/profile/:id`), sin menú lateral en escritorio (como Facebook): portada (degradado de marca), foto, nombre, cargo · área, cumpleaños, contadores, «Te sigue».
  - Pestañas **Todo** (Datos + 9 fotos a la izquierda, publicaciones a la derecha) · **Información** (dos columnas: cargo, área con enlace, jefe directo con enlace, correo, cumpleaños, desde cuándo) · **Seguidores** (Seguidores y Seguidos lado a lado) · **Fotos** (con galería). Subrayadas en escritorio, píldoras en teléfono; la pestaña va en la URL (`?tab=`).
  - Propio: «Editar perfil» (foto → WebP 512 px, quitar foto, presentación de 280). Ajeno: Seguir y Enviar correo.
- [x] **Directorio** (`/people`): buscador (nombre, correo, cargo, área) y filtro por área en la URL, tarjetas de igual alto en 1–4 columnas, «Seguir» suave, 25 por página con «Ver más», esqueletos.
- [x] **Organigrama** (`/people/org`) con **d3-org-chart 3.1.1** (la misma de antes, ahora desde npm y cargada solo en esa pestaña): tarjetas foto › nombre (→ perfil) › cargo › área, Ajustar, Abrir todo, Cerrar, acercar/alejar, buscador que centra y resalta la cadena de mando. Primera vista nunca menor a 70 % y con la raíz arriba; ramas 250 ms; sin animación con «reducir movimiento».
- [x] Enlaces al perfil desde autores de publicaciones, comentarios, sugerencias, seguidores y organigrama; «Ver mi perfil» en el menú de cuenta.
- [x] Fotos de perfil con caché por sesión (se descargan una sola vez; se liberan al cerrar sesión).
- [ ] Filtros de género y estado civil del directorio (la API ya los tiene; **(decidir)** si se muestran en la interfaz).
- [ ] Imagen definitiva de la portada del perfil.
- [ ] Organigrama con más de 10 niveles (cargar ramas con `?root=` al abrirlas).

### Tanda 4 — Avisos (hecha, noviembre 2026)
- [x] Página **Avisos** (`/notifications`): Todos · No leídos (en la URL `?filter=unread`), agrupados por día (Hoy · Ayer · Esta semana · Anteriores), 25 por página con «Ver avisos anteriores», esqueletos y estados vacíos («Estás al día»).
- [x] No leído: tinte azul, negritas y punto. Tocar un aviso lo marca como leído y lleva a su enlace. Menú «…»: marcar leído/no leído y eliminar. «Marcar todo como leído».
- [x] Todo es optimista y el contador de la campana / barra / menú lateral se actualiza al instante (y cada minuto con el servidor).
- [x] Íconos y colores: el servidor manda nombres del diseño anterior (`bx-heart`, `primary`…); se traducen a Lucide y a la marca en `features/notifications/utils/appearance.ts`.
- [x] **Detalle de publicación** (`/posts/:id`, a donde llevan los avisos): texto completo; `?comments=1` abre los comentarios.
- [x] Avisos automáticos de la red social: reacciones (a posts y comentarios), comentarios, respuestas y seguidores. Clave por evento: sin duplicados al cambiar de emoji y se retiran al deshacer o eliminar (12 pruebas).
- [ ] Agrupar avisos («Ana y 3 personas más reaccionaron…») y preferencias por persona (qué avisos recibir).
- [ ] Push (service worker, permiso del navegador, llave privada VAPID).

### Tanda 5 — Documentos (en curso, noviembre 2026)
- [x] `/documents`: Todos · Míos · Compartidos conmigo, búsqueda y categorías (en la URL), filas con ícono por tipo de archivo, versión vigente, tamaño y privacidad; esqueletos y vacíos.
- [x] Subir (con permiso `documents.documents.create`): archivo (arrastrar o elegir, ≤ 20 MB), título propuesto, categoría, descripción, privacidad Toda la empresa / Departamentos.
- [x] `/documents/:id`: ficha, Descargar (con sesión, nombre original), historial de versiones (línea de tiempo), Nueva versión, Restaurar y Eliminar para quien lo administra.
- [x] Editar la ficha (título, descripción, categoría, privacidad) y compartir con **personas** (buscador del directorio con chips), también al subir.
- [x] Nueva versión en una hoja propia: archivo + «¿Qué cambió?».
- [ ] Crear las categorías reales en el admin **(decidir: las define el responsable)**.

### Tanda 6 — Noticias (blog) (noviembre 2026)
- [x] `/blog`: la más reciente destacada y las demás en cuadrícula; búsqueda y categorías (en la URL); «Mis artículos» (borradores y programados) para quien puede escribir.
- [x] `/blog/:id`: portada (con sesión), categoría, autor, minutos de lectura, contenido HTML del servidor (`.ws-article`), reacciones con emoji («Ver todo») y comentarios con respuestas en la misma página.
- [x] `/blog/new` y `/blog/:id/edit` (permiso `blog.articles.create`; editar y eliminar solo su autor): portada (se convierte a WebP), título, resumen, categoría, editor **Tiptap** (títulos, negritas, cursiva, subrayado, tachado, enlaces, listas, citas, separador) y estado Borrador / Publicar ahora / Programar.
- [x] Comentarios reutilizables: `CommentsPanel` + `CommentSource` (muro y blog comparten la misma UI; en el blog sin reacciones por comentario).
- [ ] Imágenes dentro del contenido (subirlas desde el editor; hoy solo portada).
- [ ] Crear las categorías reales y el rol de quién escribe en el admin (en local hay «Anuncios», «Logros», «Celebraciones», «RRHH» y el rol «Comunicación» de prueba).
- [ ] Avisar cuando sale una noticia nueva **(decidir)**.

### Tanda 7 — Marketplace (noviembre 2026)
- [x] `/marketplace`: cuadrícula (2 a 4 columnas) con foto, precio («A tratar» si no hay), título y quién vende; búsqueda, categorías, «Mostrar vendidos» y «Mis anuncios» (todo en la URL).
- [x] `/marketplace/:id`: fotos con miniaturas y galería a pantalla completa (la misma del muro), precio, categoría, descripción y «Contactar» (abre el perfil de quien vende).
- [x] Publicar y editar en una hoja: hasta 10 fotos (se convierten a WebP; la primera es la portada), título, precio, categoría y descripción. Quien lo publicó lo marca como vendido / disponible otra vez o lo elimina.
- [x] API: agregar fotos a un anuncio publicado (`POST /listings/:id/images/`) y quitar una (`DELETE /images/:id/`), con pruebas.
- [ ] Reordenar fotos (elegir otra portada).
- [ ] Contacto privado (mensaje dentro de la app) **(decidir)**; hoy «Contactar» lleva al perfil.

### Tanda 8 — Mesa de ayuda (noviembre 2026)
- [x] `/helpdesk`: «Mis tickets» para todos; quien atiende un departamento ve además «Por atender» (su cola, con «Sin responsable») y «Asignados a mí». Filtros Activos / Resueltos / Cerrados / Todos y búsqueda por título o folio (en la URL). En «Mis tickets», un resuelto sigue en Activos hasta que se confirma.
- [x] Nuevo ticket en una hoja: categoría agrupada por el departamento que la atiende (con su ayuda), título, descripción y hasta 5 archivos.
- [x] `/helpdesk/:id`: conversación con el historial intercalado, adjuntos descargables con sesión, notas internas en ámbar (solo agentes) y caja para responder (Ctrl+Enter envía).
- [x] Panel del agente: Tomar ticket, estado, prioridad, responsable y categoría (cambiarla a otro departamento lo transfiere, con confirmación).
- [x] Quien lo levantó confirma la solución («Sí, cerrar») o lo reabre; también puede cerrarlo si ya no lo necesita.
- [x] Los avisos de tickets abren `/helpdesk/:id` (antes `/helpdesk/?ticket=`; la lista redirige los avisos viejos).
- [x] «Otro» para problemas que no están en la lista: el nuevo ticket elige el problema en un select con búsqueda (`components/ui/Combobox.tsx`, reutilizable: teclado, grupos, sin acentos) agrupado por departamento, con «Otro» siempre al final. «Otro» queda sin clasificar, lo ven los agentes de todos los departamentos (filtro «Sin clasificar» en «Por atender») y el que sepa de qué trata lo clasifica desde el panel. 4 pruebas.
- [ ] Crear las categorías reales y quién atiende en el admin (en local hay 8 categorías de prueba en Tecnología, RRHH y Operaciones, y el rol «Soporte TI» para Beto).

### Tanda 9 — Formularios (noviembre 2026)
- [x] API `/api/forms/`: crear (permiso `forms.forms.create`, migración que lo da de alta), editar, abrir/cerrar, eliminar (suave); guardar todas las preguntas juntas (las opciones con respuestas se archivan; una pregunta con respuestas no cambia de tipo); responder con validación por tipo y errores por pregunta; un envío por persona; resultados por pregunta y CSV para Excel. 7 pruebas.
- [x] `/forms`: Por responder · Todos · Mis formularios (con estado y número de respuestas), búsqueda.
- [x] `/forms/:uuid`: responder (respuesta corta, párrafo, opción única, casillas con mín./máx. y «Otro», desplegable, escala, estrellas, cuadrículas, fecha y hora), errores junto a cada pregunta, pantalla de «¡Gracias!».
- [x] `/forms/:uuid/edit`: título, descripción, una respuesta por persona, cierre automático, Publicar / Cerrar / Copiar enlace; preguntas con tipo, ayuda, opciones, filas y columnas, escala, obligatoria, orden aleatorio, subir/bajar, duplicar y eliminar; aviso si sales sin guardar.
- [x] `/forms/:uuid/results`: barras por opción con conteo y %, escala con promedio, cuadrícula con intensidad, respuestas de texto y descarga en CSV.
- [ ] **(decidir)** Respuestas anónimas, secciones y saltos, carga de archivos, quién ve resultados además de quien lo creó.
- [ ] Avisar cuando se publica un formulario o está por cerrar.

### Tanda 10 — Calendario (solo visual, noviembre 2026)
- [x] `/calendar`: cuadrícula del mes (lunes a domingo), mes anterior/siguiente y «Hoy», día elegido con su detalle; cumpleaños desde la API que ya existe (`/api/accounts/birthdays/`: hoy y próximos 30 días).
- [ ] **(autorizar)** Cumpleaños de cualquier mes: `GET /api/accounts/birthdays/?month=AAAA-MM` (solo ese mes; día y mes, nunca el año).
- [ ] **(autorizar)** Eventos de la empresa (app y API nuevas): qué son, quién los crea, quién los ve, confirmación de asistencia.
- [ ] **(decidir)** Mostrar el cierre de formularios abiertos en el calendario (hoy la lista de formularios no filtra por mes).

### Tanda 11 — Búsqueda general (noviembre 2026)
- [x] API de publicaciones: filtro `?q=` en `/api/social/posts/` (texto; respeta «Solo seguidores»), con prueba. Sin API nueva.
- [x] `/search` («Buscar» del menú): consulta en paralelo Personas, Publicaciones, Documentos, Noticias, Formularios, Marketplace y Mesa de ayuda con `page_size=5`; coincidencias resaltadas; «Ver todos» abre la sección con la búsqueda puesta; texto en la URL.
- [ ] Avisos oficiales: no existen todavía (los avisos son notificaciones personales).
- [ ] **(autorizar)** Si pesa hacer 7 peticiones por búsqueda: una API única `/api/search/`.

---

## Pendientes heredados (backend y decisiones)

### Acceso
- [ ] Google con JWT: Google Identity Services en React → `POST /api/auth/google/` (validar con `adapters.py`). Credenciales OAuth pendientes del responsable de Google Workspace.
- [ ] Foto de perfil desde Google en la primera entrada.
- [ ] Fotos protegidas: evaluar URLs firmadas de corta duración en lugar de descargar blobs (feed con muchas imágenes).
- [ ] Varias pestañas haciendo refresh a la vez (rotación) — ver `backend/autenticacion.md`.

### Social
- [ ] **(decidir)** Política de borrado definitivo (días que se conservan posts/comentarios eliminados) y comando `purge_deleted`.
- [x] Moderación con `.delete.all` (posts, comentarios, estados, noticias, anuncios, formularios) y `.update.all` (noticias, anuncios, formularios). Se asigna con un rol.
- [ ] Editar adjuntos de una publicación; «Ver más» en textos largos.
- [ ] Audiencias por roles/áreas; que `social.posts.view.all` deje ver publicaciones de «Solo seguidores» (hoy solo abre la sección); categorías (`PostCategory`).
- [ ] Producción: media con X-Accel-Redirect / X-Sendfile (rangos de video); compresión/miniatura de videos.

### Catálogos
- [ ] **(decidir)** Licencia de Noto Animated Emoji (si es CC BY 4.0 → atribución).
- [ ] Caché de la API de catálogos (`Cache-Control`/`ETag`).

### Avisos y push
- [ ] Envío push (llave privada VAPID + `pywebpush`), limpiar suscripciones 404/410. **(decidir)** si cerrar sesión borra la suscripción.
- [ ] Generar avisos desde documentos, formularios y RRHH/sistema (social y mesa de ayuda ya los generan).

### Organización
- [ ] Capturar en el admin departamento y jefe de cada persona real.
- [ ] Organigrama con más de 10 niveles (cargar ramas con `?root=`).
- [ ] **(decidir)** Tabla `Employee` (número, fecha de ingreso, puesto) y `Position` (catálogo o texto).

### Documentos y archivos
- [ ] **(decidir)** ¿Avisar cuando sale una versión nueva? ¿«Departamentos» incluye subdepartamentos?
- [ ] Producción: antivirus (ClamAV).

### Mesa de ayuda
- [ ] **(decidir)** SLA por prioridad, quién elige prioridad, cierre automático, encuesta.

### Blog y Marketplace
- [x] Editor enriquecido del blog: **Tiptap** (MIT). Pendiente: imágenes dentro del contenido.
- [ ] **(decidir)** Marketplace: contacto privado, preguntas públicas, moderación, vigencia, categorías iniciales.

### Formularios
- [x] Quién crea: permiso `forms.forms.create` (asignado por rol en el admin; en local, rol «Recursos Humanos» de Carla).
- [ ] **(decidir)** Respuestas anónimas, secciones y saltos, carga de archivos.

### Permisos y vacaciones
- [ ] **(decidir)** Reglas con RH: días por antigüedad (LFT 2023), año calendario o aniversario, medios días, acumulación, flujo de aprobación.

### Correo
- [ ] Crear `no-reply@`, configurar SMTP en `.env` de producción y probar; decidir qué avisos salen por correo.

### Infraestructura
- [ ] Reconstruir el repositorio git con `.gitignore` (excluir `.env`, `.venv/`, `node_modules/`, `db.sqlite3`, `media/`, `dist/`, `staticfiles/`).
- [ ] Modo oscuro.
- [ ] PostgreSQL (configuración, migración de datos, integridad); búsqueda sin acentos (`unaccent`).
- [ ] Limpiar/reiniciar migraciones al final de la etapa; borrar datos de prueba (`demo`).
- [ ] Producción: servidor, HTTPS, estáticos, media privada, despliegue del frontend (mismo dominio que la API recomendado).
