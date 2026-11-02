# Backlog de Workspace (trabajo por tandas)

Lista viva de lo que falta. Se trabaja **por tandas**: al cerrar una tanda se marca aquí lo hecho y se ajusta lo pendiente. Cuando se pregunte «¿qué nos falta?», la respuesta sale de este archivo.

Estados: `[ ]` pendiente · `[~]` en curso · `[x]` hecho · **(decidir)** necesita una decisión del responsable del proyecto.

---

## Hecho

- [x] Reinicio de `apps.social`: modelo `Post` de solo texto.
- [x] API `/api/social/posts/` (listar paginado, crear, detalle) con sesión + CSRF.
- [x] Portada como *shell*: el feed se pide a la API (`feed.js`) y usa `<template>` de `post_card.html`.
- [x] Login/logout (`/accounts/login/`, `/accounts/logout/`).
- [x] Saltos de línea en posts; fechas relativas con Day.js.
- [x] jQuery para el JS; Bootstrap 5.3 como base con tema propio (primario `#0066CC`, secundario `#F4C600`); fondo de página `#F5F6FA` con cards blancas.
- [x] Limpieza de plantillas, CSS y dependencias sin uso (`django-htmx`, restos de «Nexo»).

---

## Tanda: navegación, páginas y pulido de interfaz — hecha

- [x] **Un solo container** para encabezado y páginas (`--ws-shell-width`); el encabezado nunca cambia de ancho. Perfil sin menú lateral (`no-sidebar`, como Facebook); Personas, Buscar, Avisos y las demás páginas sin widgets usan todo el ancho (`ws-container--fill`).
- [x] **Personas** rediseñado: 4 columnas en escritorio, tarjetas con nombre › cargo › área (etiqueta) › acción, alturas iguales y «Seguir» suave (`ws-btn-soft`).
- [x] **Buscar** como página propia (`/search/`): filtros Todo · Personas · Documentos · Avisos · Formularios; «Personas» busca en el directorio; lo demás «Próximamente». Sin búsquedas recientes de prueba. `/#buscar` redirige.
- [x] **Avisos** con la jerarquía del tema: encabezado + subtítulo, todo el ancho; no leído con tinte azul, negritas y punto.
- [x] **Páginas nuevas** con aviso «en construcción»: Calendario, Noticias, Documentos, Formularios, Marketplace, Ayuda, Términos y Privacidad (estas dos públicas).
- [x] **Menú:** Calendario, Noticias y Marketplace en *Principal*; Ayuda en *Cuenta*; pie con Términos, Privacidad y ©. **Mi cuenta en el encabezado** (avatar + nombre, menú: Ver mi perfil · Ayuda · Cerrar sesión); se quitó la tarjeta de perfil del menú.
- [x] **Calendario** (`/calendar/`, FullCalendar 6 local): Mes, Semana y Agenda (Agenda por defecto en teléfono), barra propia de Bootstrap, aviso de que aún no hay fechas.
- [x] **Galería (lightbox)** de las publicaciones con PhotoSwipe 5: solo los medios del post, zoom desde la miniatura, cerrar arrastrando, teclado y foco accesibles.
- [x] **Login:** pie legal dentro de la tarjeta, tarjeta centrada en el alto visible (`100dvh`) en el teléfono y emojis animados (Noto) que se animan una vez.
- [x] **PWA — manifest e íconos:** `/manifest.webmanifest` en todas las páginas, íconos del logo (192, 512, maskable, iPhone) y favicon (`runscript make_icons`).
- [x] **Correo — preparado:** `send_email()` + plantillas + settings por `.env` (ver pendiente en «Intranet y navegación»).
- [x] **JWT instalado** (`djangorestframework-simplejwt`, `SIMPLE_JWT` configurado) sin activar; los pasos para activarlo están en `config/settings/base.py`.
- [x] `showcase.html` actualizado: «Disponible hoy» solo con lo terminado, «En desarrollo» lo que solo tiene modelo/API/página, y sección «Arquitectura» (Django hoy, React posible a futuro).

### Pendiente de esta tanda

- [ ] PWA: service worker (sin conexión y base para push) y botón propio «Instalar app» (`beforeinstallprompt`). Probar la instalación en un teléfono por HTTPS.
- [ ] Calendario: API de fechas (eventos, cumpleaños, avisos con fecha) y conectarla en `calendar.js` (`events`).
- [ ] Contenido de Ayuda (guías, preguntas frecuentes) y textos de Términos y Privacidad (los redacta o revisa Legal).
- [ ] Fotos de prueba de los bots: la fuente de `scripts/fake_media.py` no tiene «í» («d□a»); usar una fuente con acentos.

---

## Tanda: catálogos y reacciones con emojis — hecha

Detalle en `docs/reaction-emojis.md`.

- [x] App `apps.catalogs` (datos de referencia compartidos entre apps).
- [x] `catalogs.Emoji` con los emojis elegidos (75 iniciales + 59 agregados = 134); JSON + migración de carga + `python manage.py load_catalogs`.
- [x] Admin de `Emoji` (ordenar, activar/desactivar; no se borra un emoji en uso).
- [x] `GET /api/catalogs/emojis/`.
- [x] `catalogs.BaseReaction` (abstracto) y `social.PostReaction` (una reacción por persona y post).
- [x] API: poner/cambiar/quitar mi reacción, resumen en cada post, «Ver todo».
- [x] Archivos Noto (SVG + Lottie) en `static/assets/emoji/` y lottie-web local bajo demanda.
- [x] UI: pastillas 20 px, «carita +», selector 36 px, animación una vez al reaccionar, «Ver todo»; sin animación con «reducir movimiento». Se quitó el botón «Me gusta».
- [x] Documentación (`AGENT.md`, `docs/architecture.md`).
- [ ] **(decidir)** Verificar licencia de Noto Animated Emoji (no se pudo confirmar; si es CC BY 4.0 → atribución).
- [x] Decidido: **un solo emoji por persona en cada post** (confirmado por el responsable del proyecto).

### Pendiente posterior de catálogos
- [ ] **Caché de la API de `catalogs`.** Son datos informativos que casi no cambian: cachear la respuesta (cabeceras `Cache-Control`/`ETag` y/o caché de Django) e invalidar al editar en el admin o al correr `load_catalogs`. **No se hace todavía.**

---

## Social (publicaciones)

- [x] Comentarios de texto en posts (modal, lista paginada, contador «x comentarios» en la tarjeta).
- [x] Respuestas a comentarios (un nivel; responder a una respuesta cuelga del mismo hilo).
- [x] Editar y eliminar comentarios propios (borrado suave; con respuestas queda «Comentario eliminado»).
- [x] Reacciones en comentarios (`CommentReaction` sobre `catalogs.BaseReaction`).
- [x] Reacciones estilo Discord (pastillas compactas) y botón «Reaccionar» con un solo ícono.
- [x] Adjuntos de imágenes y videos en posts (sin documentos, decidido): WebP en el navegador (`Workspace.procesarAWebP`), validación por contenido en el servidor (`apps/core/uploads.py`), archivos `<id>.<ext>`, entrega autorizada.
- [ ] Visor de imágenes a pantalla completa (tocar una foto del post o de la pestaña «Fotos» del perfil; hoy abre la imagen en otra pestaña).
- [ ] Probar subida de video en un dispositivo real (validado en pruebas automáticas, no en el navegador).
- [ ] Producción: entregar media con el servidor web (X-Accel-Redirect / X-Sendfile) para rangos de video (adelantar/retroceder en Safari) y no ocupar a Django.
- [ ] Videos: evaluar compresión/miniatura en el servidor (hoy se guardan tal cual, máx. 100 MB).
- [x] Editar texto y eliminar publicaciones propias (menú «…» solo para el autor; el servidor valida). Borrado suave con `deleted_at`.
- [ ] **(decidir)** Política de borrado definitivo: cuántos días se conservan posts/comentarios eliminados (y sus archivos) antes de purgarlos; luego un comando `purge_deleted` programado.
- [ ] Moderación: permiso de negocio para que RRHH/TI eliminen publicaciones o comentarios ajenos (p. ej. `social.posts.delete.any`).
- [ ] Restaurar publicaciones eliminadas desde el admin (hoy: poner `deleted_at` vacío a mano).
- [ ] Editar adjuntos de una publicación (hoy solo se edita el texto).
- [x] Se quitó «Compartir» (en su lugar va «x comentarios»). Si vuelve, será una decisión nueva.
- [ ] «Ver más» para textos largos.
- [ ] Audiencias por roles/áreas y permiso `social.posts.view.all` (hoy: empresa / solo seguidores).
- [ ] Categorías de publicación (`PostCategory`).

## Nuevas apps

- [x] **Blog — modelo** (referencia: diseño «Noticias»). App `apps/blog`: `Article` (título, slug, resumen, contenido **HTML** limpiado al guardar con `nh3`, portada, categoría, autor, borrador/publicado, fecha de publicación —permite programar—, borrado suave), `ArticleCategory` (chips de filtro, desde el admin), `ArticleReaction` (hereda de `catalogs.BaseReaction`) y `ArticleComment` (respuestas de un nivel). «Post» queda solo para el feed.
- [x] **Blog — API** (`/api/blog/`, detalle en `docs/api.md`): artículos (lista de publicados con filtros, `?mine=1` con borradores y programados, crear/editar/borrar con portada WebP), reacciones, comentarios con respuestas, categorías y `permissions/`. Escribir requiere el permiso de negocio `blog.articles.create`; editar y borrar, solo el autor.
- [ ] Blog: vistas y editor enriquecido. **(decidir)** editor: CKEditor 5 (desde la v44 pide clave de licencia; GPL o comercial) vs. TinyMCE / Quill / Jodit; subida de imágenes dentro del contenido (`ArticleImage` + endpoint propio, en lugar de CKFinder, que es de pago); quién puede publicar (permiso); reacciones a comentarios del blog.
- [x] **Marketplace — base.** App `apps/marketplace`: `Listing` (título, descripción, precio opcional —vacío = «A tratar»—, estatus Disponible/Vendido con `sold_at`, categoría opcional, borrado suave), `ListingImage` (hasta 10 fotos WebP validadas con `apps.core.uploads`, entregadas por vista autorizada) y `ListingCategory` (desde el admin, para filtros). API `/api/marketplace/`: `listings/` (lista con filtros `status`, `category`, `seller`, `q`; publicar en multipart), `listings/<id>/` (ver, editar campos o estatus, borrar; solo quien publicó), `categories/`, `images/<id>/file/`.
- [ ] Marketplace: pantallas, agregar/quitar fotos a un artículo ya publicado, reacciones (`ListingReaction` heredando de `catalogs.BaseReaction`). **(decidir)** contacto privado (correo / chat interno / herramienta externa), preguntas públicas, moderación, vigencia de anuncios, si salen en Inicio y lista inicial de categorías.

## Estructura, mesa de ayuda y permisos (tandas 1–5)

Alcance de RH limitado a estructura y permisos: **sin nómina, sueldos ni expediente**. Hecho (2026-10-30): departamentos, organigrama, adjuntos seguros y mesa de ayuda (API). **Pendiente de definir con el responsable:** tabla de empleados (abajo) y permisos/vacaciones (tanda 5).

### Departamentos y organigrama — hecho (API)

- [x] App `apps.org`: `Department` (nombre único sin distinguir mayúsculas, `parent` para subáreas, `head` responsable, activo; el admin impide ciclos).
- [x] `User.department` pasó de texto a la tabla (migración `accounts.0007`: los textos existentes se convirtieron en departamentos) y se agregó `User.manager` (jefe directo; el admin impide ciclos). Personas, Perfil, Buscar y sugerencias («mismo departamento primero») ya usan la tabla. La API sigue mandando `department` como nombre y agrega `department_id`.
- [x] API `/api/org/departments/` y `/api/org/chart/` (árbol por jefe directo, `?root=`, `?depth=`, `reports_count`, `unassigned_count`); `/api/accounts/users/?department=<id>`; `manager` en el perfil.
- [x] Pestaña «Organigrama» (`/people/org/`, pestañas Directorio · Organigrama) con **d3-org-chart 3.1.1** (+ d3 7.9.0, d3-flextree 2.1.2) en `static/assets/vendor/d3-org-chart/`: tarjetas foto › nombre (enlace al perfil) › cargo › departamento, abrir/cerrar ramas, Ajustar, Abrir todo, Cerrar, zoom, arrastrar, buscador que centra y resalta la cadena de mando. Primer encuadre legible (no encoge por debajo de 70 %); sin animación de entrada, 250 ms al abrir ramas, nada con «reducir movimiento». Controles solo con ícono en teléfono.
- [ ] Mostrar jefe directo y departamento (con enlace) en el perfil.
- [ ] Capturar en el admin el departamento y el jefe directo de cada persona real. (En desarrollo, los bots ya tienen jefes: Gabriel Luna arriba, Elena Vargas con su equipo.)
- [ ] Organigrama con más de 10 niveles: hoy se piden 10 (`?depth=10`); cargar ramas más profundas con `?root=` al abrirlas.

### Tabla de empleados — por definir

- [ ] **(decidir)** `Employee` (uno a uno con `User`): número de empleado, **fecha de ingreso**, puesto. Al crearla se mudan ahí `department` y `manager` (hoy en `User`), y quizá `job_title`, `birth_date`, `gender`, `marital_status`. No todo usuario es empleado (admins, cuentas de servicio).
- [ ] **(decidir)** `Position` (puesto): catálogo o texto libre.

### Adjuntos seguros — hecho

- [x] `apps/core/uploads.py` → `check_document_upload`: lista permitida por **contenido real**, máx. 20 MB. PDF (sin JavaScript, `Launch` ni archivos incrustados), `.docx`/`.xlsx`/`.pptx` (sin macros, ActiveX, objetos OLE ni ejecutables dentro; con tope contra bombas zip), PNG/JPEG/WebP decodificables, `.csv`/`.txt` (UTF-8 o Windows-1252, sin binarios). Se rechazan ejecutables, scripts, HTML, SVG, zip, `.doc`/`.xls` viejos y Office con macros aunque se renombren.
- [x] Nombre en disco `<id>.<ext>` (extensión según el contenido); entrega por vista autorizada con `nosniff`; lo que no es imagen sale como descarga con su nombre original.
- [ ] Producción: escaneo antivirus (ClamAV) — la revisión de PDF no inspecciona objetos comprimidos.
- [~] Usarlo en Documentos (hecho: versiones) y Formularios cuando acepten archivos.

### Mesa de ayuda — hecho (API)

- [x] App `apps.helpdesk`: `TicketCategory` (departamento que atiende, incidencia/solicitud), `Ticket` (folio `HD-00042`, estado, prioridad, responsable, fechas de primera respuesta / resuelto / cerrado), `TicketComment` (públicos y **notas internas**), `TicketAttachment`, `TicketEvent` (historial). Admin completo.
- [x] Agentes: responsable del departamento + personas del departamento con `helpdesk.tickets.attend`; `helpdesk.tickets.view.all` consulta todo sin atender (ambos permisos se crean en la migración `helpdesk.0002`).
- [x] API `/api/helpdesk/` (ver `docs/api.md`): levantar con hasta 5 archivos, lista con `scope` mine/assigned/queue y filtros, detalle con conversación e historial, atender (estado, prioridad, asignar, transferir de categoría), comentar, candidatos a asignar, descarga autorizada, `me/`.
- [x] Avisos con `notify()` (nuevo, asignado, respuesta, cambio de estado, transferido), enlazados a `/helpdesk/?ticket=<id>`. Página `/helpdesk/` en construcción y enlace «Mesa de ayuda» en el menú.
- [x] Valores por omisión aplicados (cambiables): estados Abierto → En proceso → En espera → Resuelto → Cerrado (final); quien lo levantó puede **cerrarlo** o **reabrirlo si está resuelto**; prioridad la ponen solo los agentes (por omisión Normal); 5 archivos por mensaje.
- [ ] Pantallas: lista (mis tickets / mi cola), levantar ticket, detalle con conversación y acciones de agente.
- [ ] Crear en el admin las **categorías** por departamento (las define el responsable) y asignar el rol con `helpdesk.tickets.attend` a los agentes.
- [ ] Avisos por correo (cuando exista `no-reply@`).
- [ ] **(decidir)** SLA / tiempos de respuesta por prioridad; si quien levanta puede elegir prioridad; cierre automático de «Resuelto» tras N días sin respuesta; encuesta de satisfacción.

### Tanda 5 — Permisos y vacaciones (`apps.leaves`)

- [ ] `LeaveType`: Vacaciones / Administrativo, `annual_days` (**12** para administrativos), si descuenta saldo, si pide documento. Es la «tabla de settings»: nada de esto va en `.env`.
- [ ] `LeaveBalance` (empleado + tipo + periodo → asignados, usados, disponibles), `LeaveRequest` (fechas, días hábiles calculados, motivo, estado) y `Holiday` (festivos, no cuentan).
- [ ] Vacaciones según antigüedad (LFT, reforma 2023: 12 días el 1.er año, +2 por año hasta 20 al 5.º, luego +2 cada 5 años) a partir de la fecha de ingreso. **Confirmar con RH.**
- [ ] **(decidir)** administrativos por año calendario o por aniversario; medios días; si los no usados se pierden o se acumulan; aprobación solo del jefe directo o jefe y luego RH.

## Cuentas y acceso

- [x] **Login nuevo** (`/accounts/login/`): un solo campo «Usuario o correo» + contraseña (`apps/accounts/backends.py` → `UsernameOrEmailBackend`; correo sin distinguir mayúsculas). Error genérico «Usuario, correo o contraseña incorrectos.» (no revela qué cuentas existen, ni si están desactivadas). Diseño móvil con encabezado de marca; escritorio a dos paneles. Mostrar/ocultar contraseña, aviso de Bloq Mayús, «Entrando…» sin doble envío.
- [x] Se quitó «Ubicación / sede» del usuario: todo el personal está en Querétaro.
- [x] Zona horaria del servidor: `America/Mexico_City` (sede Querétaro). La API manda fechas ISO 8601 con desfase y el navegador las muestra en la zona de quien las ve (el `title` de la fecha incluye la zona, p. ej. «(GMT-6)»).
- [x] **Confirmado:** el personal usa Gmail con el dominio **@orienta.soy** (Google Workspace).
- [x] **«Continuar con Google»** (`django-allauth`), listo en código; **falta poner las credenciales**:
  - Solo cuentas del Workspace `@orienta.soy` (`GOOGLE_ALLOWED_DOMAIN`): se pide a Google con `hd` y el servidor exige dominio del correo, correo verificado por Google y `hd` correcto (`apps/accounts/adapters.py`). Gmail personal u otros dominios → de vuelta al login con «Usa tu cuenta de Google @orienta.soy».
  - Primera vez = cuenta creada sola (nombre y correo de Google, usuario generado del correo, sin contraseña). Si ya existe un usuario con ese correo, entra a esa cuenta y queda vinculada; por seguridad (protección de allauth) su contraseña local se desactiva, TI puede poner otra si hace falta.
  - Cuentas desactivadas no entran. Cancelar o errores de Google → login con mensaje (sin pantallas de allauth).
  - El botón hace POST con CSRF; un GET a `/accounts/google/login/` no inicia nada. Sin credenciales: botón deshabilitado en desarrollo, oculto en producción.
  - De allauth solo se usa Google: registro con contraseña, recuperar contraseña, correos y conexiones redirigen al login.
  - **Pendiente del responsable de Google Workspace de orienta.soy:** crear en Google Cloud un «ID de cliente OAuth» → aplicación web, pantalla de consentimiento **Interna**. URI de redirección autorizados: `http://localhost:8000/accounts/google/login/callback/` (desarrollo) y `https://<dominio>/accounts/google/login/callback/` (producción). Poner `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` en `.env` y reiniciar el servidor.
- [ ] Foto de perfil desde Google en la primera entrada (descargarla y convertirla a WebP).
- [ ] Recuperar contraseña: con Google ya no hace falta para el personal; para cuentas solo con contraseña, hoy se pide a Soporte TI.
- [ ] Límite de intentos de inicio de sesión (p. ej. `django-axes`) antes de producción.

## Intranet y navegación

- [ ] Avisos reales (modelo, API) — hoy son datos de demostración.
- [x] **Avisos = notificaciones** — solo tabla y vista (decidido). App `apps/notifications`, modelo **general** `Notification` para todo Workspace (no solo posts): para quién, de quién (opcional), `kind` libre «app.evento», título, texto, ícono, color, enlace y objeto de origen genérico opcional. API de lista (25 por página). Página «Avisos» (`/notifications/`) a la que llevan la campana y la pestaña «Avisos»; tarjetas como el diseño de referencia. Se quitaron los avisos de demostración.
- [x] **Push PWA — tabla.** `notifications.PushSubscription`: un registro por dispositivo/navegador donde la persona aceptó notificaciones (endpoint único + llaves `p256dh`/`auth` de la Push API, navegador, fecha de alta y último envío). Visible en el admin.
- [x] **Avisos — API completa:** leer una, marcar leída / no leída, marcar todas, contador de no leídas, eliminar, `?unread=1` y servicio `notify()` para las demás apps. Push: `push/config/` (llave pública VAPID desde `.env`), registrar / listar / quitar dispositivos.
- [ ] Push PWA: envío (llave privada VAPID + p. ej. `pywebpush`) al crear un aviso, actualizar `last_used_at` y borrar suscripciones que respondan 404/410; service worker en el frontend. **(decidir)** si cerrar sesión borra la suscripción de ese dispositivo.
- [ ] Avisos: **generarlos** desde las apps (social: reacciones, comentarios, respuestas, seguidores; luego documentos, formularios, RRHH/sistema) con una función común; sin duplicar al cambiar de emoji y retirándolos si se deshace la acción.
- [ ] Avisos: marcar como leídos (al tocar / «Marcar todo»), contador en la campana y en la pestaña, y consulta periódica.
- [ ] Avisos: agrupar («Ana y 3 personas más reaccionaron…»), preferencias por persona, ocultar los de objetos eliminados o no visibles (usando el objeto de origen) y avisos masivos de RRHH/sistema a toda la empresa o a un área.
- [ ] Actualización en vivo del feed (reacciones/comentarios de otros sin pulsar «Recargar»). Sin WebSockets en esta etapa: evaluar sondeo periódico.
- [~] Búsqueda: página `/search/` lista; con «Personas» ya busca (directorio). Falta la búsqueda general (API de publicaciones, noticias, documentos, formularios).
- [x] Accesos rápidos de Inicio llevan a páginas reales (Documentos y Formularios, en construcción).
- [x] Perfil (`/profile/` y `/profile/?user_id=<id>`), diseño móvil: portada estática, foto, nombre, cargo · área, pestañas (hoy Todo / Información / Seguidores / Fotos; «Fotos» = todas las imágenes de sus publicaciones), «Editar perfil» (foto y presentación) y «Enviar correo» en perfiles ajenos. Autores del feed y comentarios enlazan al perfil.
- [x] Perfil en pantallas grandes (≥ 992px): encabezado horizontal (portada ancha, foto a la izquierda, nombre · cargo · área · cumpleaños, acciones a la derecha) y pestañas subrayadas como Facebook: **Todo** (Datos + 9 fotos a la izquierda, publicaciones a la derecha) · **Información** (dos columnas) · **Seguidores** (Seguidores / Seguidos a dos columnas, la misma lista del modal) · **Fotos**. Teléfono: las mismas 4 pestañas como píldoras.
- [ ] Imagen definitiva de la portada estática (hoy: degradado de marca en `theme.css`, `.ws-profile-cover`).
- [ ] **(decidir)** Más datos del perfil: extensión/teléfono. (Jefe directo: ya en la API del perfil.)
- [x] Barra de scroll sin «salto» al abrir/cerrar modales y offcanvas (`scrollbar-gutter: stable` y sin la compensación de Bootstrap; barra delgada con color de marca).
- [x] Seguir personas (inmediato, sin solicitud — decidido) con contadores, «Te sigue» y listas de seguidores/seguidos en el perfil.
- [x] Audiencia por publicación: «Toda la empresa» o «Solo seguidores» (al crear y al editar). Inicio muestra lo de toda la empresa + lo «solo seguidores» de quien sigues (decidido).
- [x] Directorio «Personas» (`/people/`): tarjetas con foto, nombre, cargo · área y botón Seguir; buscador por nombre, correo, cargo o área; 25 por página con «Ver más». Enlazado desde «Directorio» en Inicio y desde el menú.
- [x] Sugerencias de a quién seguir (widget «Personas que quizás conozcas»).
- [ ] Búsqueda sin acentos (hoy «saenz» no encuentra «Sáenz»; en PostgreSQL se resuelve con `unaccent`).
- [x] Organigrama → `/people/org/` (ver «Estructura, mesa de ayuda y permisos» › Departamentos y organigrama).
- [ ] Notificar «X empezó a seguirte» (incluido en «generar notificaciones»).
- [x] **Documentos — modelos, servicios y API** (`apps/documents`, `/api/documents/`). `DocumentCategory` (admin), `Document` (título, descripción, categoría, dueño, borrado suave) con **privacidad**: Toda la empresa · Departamentos (los elegidos, sin subdepartamentos) · Personas (las elegidas); el dueño, `documents.documents.manage` y `documents.documents.view.all` (solo lectura) ven todo. `DocumentVersion`: cada archivo es una versión numerada con nota de qué cambió; nunca se sobrescribe, la vigente es la última y **restaurar** copia una anterior como versión nueva («Restaurada de la v1»). Archivos con `check_document_upload`, descarga autorizada por versión. Subir: `documents.documents.create`; administrar: dueño o `manage`.
- [ ] Documentos: **pantalla** (`/documents/`: lista con categorías y búsqueda, subir, detalle con historial de versiones, compartir).
- [ ] **(decidir)** Documentos: ¿avisar (notificación) cuando sale una versión nueva? ¿a quién, si es de toda la empresa? ¿«Departamentos» incluye subdepartamentos?
- [x] **Formularios — modelo** (estilo Google Forms). App `apps/form_builder` (se descartó `forms` por chocar con `django.forms`). Modelos con nombres que no chocan con Django/DRF: `DynamicForm` (no `Form`; título, descripción, dueño, borrador/abierto/cerrado, abre/cierra el, un envío por persona, uuid para el enlace, borrado suave), `Question` (respuesta corta / párrafo, obligatoria, orden), `Submission` (no `Response`; quién y cuándo) y `Answer` (una por pregunta, texto).
- [x] Formularios: preguntas **cerradas** (modelo). `Question.Kind`: opción única (radio), casillas, desplegable, escala lineal, calificación, cuadrículas de opción única y de casillas, fecha y hora; «Otro» con texto, orden aleatorio, mín./máx. de casillas, escala 0/1 a 2–10 con etiquetas. `QuestionOption` (rol opción/fila, orden, `archived_at`; texto único por pregunta) y `Answer.options` por la tabla `AnswerChoice` (una fila por opción elegida, `RESTRICT`: una opción con respuestas se archiva). `Answer` suma `row` (cuadrículas, una respuesta por fila), `number`, `date` y `time`. Migración `0002_closed_questions` (solo agrega; los datos existentes no cambian).
- [ ] Correo: **preparado** (`apps/core/mail.py` → `send_email()`, plantillas en `templates/emails/`, settings en `.env`; sin SMTP sale en la consola). Falta: crear la cuenta `no-reply@`, poner `EMAIL_HOST`/usuario/contraseña de aplicación en `.env` de producción, probar con `python manage.py sendtestemail`, y decidir qué avisos se mandan por correo (y envío en segundo plano si son masivos).
- [ ] Formularios: **gráficas/resumen** de respuestas cerradas (conteos por opción con `AnswerChoice`, por número en escalas, por fila × columna en cuadrículas). **(decidir)** secciones y saltos según respuesta, carga de archivos, «una respuesta por columna» en cuadrículas, editar después de enviar.
- [ ] Formularios: vistas, API, validar obligatorias y «un envío por persona» en el servicio, resultados/exportar. **(decidir)** respuestas anónimas, secciones, quién puede crear formularios.
- [x] `django-extensions` + carpeta `scripts/` (`runscript`). Bots de desarrollo en `scripts/bots/`: `create_bots` (8 bots `bot.*` con personalidad, seguimientos no simétricos y a administración; contraseña «1234», solo con DEBUG o `WORKSPACE_ALLOW_BOTS=1`) y `create_posts` (publicaciones con la voz de cada bot, todos los tipos, interacciones que respetan la visibilidad).
- [ ] Feed: volver `data-ws-page-size` a 25 (o quitarlo) cuando haya datos reales; hoy pide 5 para que se note el scroll infinito.
- [x] API: todas las listas paginan con `SafePageNumberPagination`: 25 por defecto, `?page_size=` para pedir menos (máx. 25). Feed con scroll infinito.

## Pantallas grandes

- [x] **Inicio en 3 columnas** (≥ 992px menú + publicaciones; ≥ 1200px + widgets). `layouts/app.html` → `.ws-shell` (cuadrícula); las páginas con `{% block aside %}` y `shell_class " has-aside"` tienen columna 3.
  - Columna 1: el mismo menú, con `offcanvas-lg` (panel lateral en el teléfono, columna fija en escritorio). En escritorio: opción activa marcada (`active_nav`; «Mi cuenta» pasó al encabezado), «Avisos» y «Buscar» (en el teléfono ya están en la barra inferior). Sin barra inferior ni botón de menú.
  - Columna 3 (widgets reales, cada uno skeleton → vacío → lista): **Cumpleaños** (`/api/accounts/birthdays/`, hoy y próximos 30 días, nunca el año; `User.birth_date` lo llena RRHH en el admin), **Personas que quizás conozcas** (`/api/social/follows/suggestions/`, misma área primero, con «Seguir»), **Avisos recientes** (3).
- [x] Las demás páginas en escritorio: sin columna 3; usan todo el ancho junto al menú (`ws-container--fill`) con el mismo container que el encabezado. El perfil va sin menú lateral.
- [x] CSS/JS sin caché vieja: en desarrollo `{% static %}` agrega `?v=<fecha de modificación>` (`apps/core/staticfiles.py`); en producción `ManifestStaticFilesStorage` (hash en el nombre, `collectstatic`). Ojo: ese procesador también lee `url(...)` dentro de comentarios CSS.
- [ ] Más widgets: aniversarios laborales (necesita fecha de ingreso; `date_joined` es la fecha de la cuenta, no del ingreso), próximos eventos, noticias destacadas (cuando exista el blog).
- [ ] Felicitar desde el widget de cumpleaños (abrir el composer con una mención).

## Diseño

- [ ] Modo oscuro: fondo `#19181A` (ya anotado en `theme.css`, sin aplicar).

## Infraestructura y cierre

- [ ] Limpiar/reiniciar migraciones al final de la etapa (se acordó no preocuparse por migraciones intermedias).
- [ ] Borrar datos de prueba locales: usuario `demo` y sus publicaciones.
- [ ] PostgreSQL (configuración, migración de datos, integridad).
- [ ] Producción: seguridad, estáticos, media privada, despliegue.
- [ ] Frontend separado (React u otro) consumiendo la API — etapa avanzada, solo si se decide (hoy todo es Django). JWT ya está instalado para ese momento.
