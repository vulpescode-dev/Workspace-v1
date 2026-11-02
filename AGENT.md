# AGENT.md — Contexto del proyecto Workspace

Lee este archivo y revisa el código real antes de modificarlo. Continúa desde el estado existente: **no recrees ni sobrescribas código funcional sin comprobarlo**. Si la documentación difiere del código, identifica la discrepancia y corrige la documentación o el código de forma explícita; no supongas que una tarea está terminada solo porque aparece aquí.

## 1. Visión del producto
## Definición oficial del producto: plataforma híbrida de colaboración e intranet

**Workspace no es solamente una red social, solamente una intranet ni un clon de Google Workspace. Es una plataforma empresarial integrada que combina tres dimensiones:**

1. **Capa social y colaboración:** publicaciones internas, feed de novedades, comentarios, reacciones, adjuntos y conversaciones alrededor de información del trabajo.
2. **Capa de intranet empresarial:** avisos oficiales, documentos corporativos, información organizada por áreas, accesos según roles y permisos, y un punto central de entrada a recursos internos.
3. **Aplicaciones de productividad integradas, inspiradas en patrones de herramientas como Google Forms:** creación y consulta de formularios, recopilación de respuestas y futuras herramientas internas. La referencia a Google es funcional, no una obligación de copiar su interfaz ni de integrar servicios de Google.

El objetivo es que una persona empleada encuentre en un solo lugar la información, comunicación y herramientas necesarias para trabajar. El feed es una puerta de entrada importante, pero **no define por sí solo todo el producto**. Documentos, avisos, formularios y futuras aplicaciones son módulos de primera clase, no accesorios de la red social.

### Modelo mental para diseñar y desarrollar

- La **intranet** define el contexto empresarial, la organización de la información, el acceso y las reglas de seguridad.
- La **capa social** facilita la difusión y colaboración en torno a la información.
- Las **apps de productividad** resuelven tareas concretas, como formularios, documentos y otras herramientas que se incorporen.
- La **navegación global** conecta estas capacidades bajo una sola experiencia, marca y sistema de diseño.

No presentar el producto como una red social pública ni reducirlo a un panel de administración. Tampoco asumir que debe replicar exactamente Facebook, Google Forms o cualquier producto de referencia. Se toman patrones útiles, se adaptan a las necesidades internas y se mantiene una experiencia coherente.

### Regla para decisiones futuras

Cuando se proponga una pantalla, modelo, aplicación o funcionalidad, identificar a qué dimensión pertenece y cómo se integra con las demás. Si una decisión solo mejora el feed pero dificulta encontrar documentos o formularios, no debe considerarse automáticamente una mejora para Workspace.



**Workspace** es una intranet empresarial y mesa de trabajo digital para aproximadamente 500 empleados, con capacidad de crecimiento. No debe sentirse como una red social pública ni como un panel administrativo genérico. Su objetivo es reunir información interna y tareas frecuentes en una experiencia móvil clara:

- Inicio con publicaciones internas, novedades y avisos.
- Avisos/notificaciones.
- Documentos y recursos compartidos.
- Formularios internos.
- Un menú central para acceder a las demás herramientas que se incorporen.
- En etapas posteriores: comentarios, reacciones, adjuntos, audiencias, usuarios, roles y permisos.

Las capturas de referencia aportadas muestran una aplicación móvil de espacios de trabajo: navegación inferior fija, tarjetas blancas redondeadas, jerarquía tipográfica clara, iconos sencillos, espacios generosos, sombras suaves, fondos claros y acentos de color. Se toma como referencia visual (los colores de Workspace son azul #0066CC y amarillo #F4C600), no se deben copiar marcas, textos ni pantallas de la aplicación de ejemplo.

## 2. Decisiones de arquitectura vigentes

- Backend: Django 5.2 LTS y Django REST Framework.
- Arquitectura: monolito modular de Django; no dividir en microservicios.
- Frontend de la etapa actual: Django Templates como *shell*, Bootstrap 5.3 como base visual (tema propio en `bootstrap-theme.css`), jQuery y datos por API.
- **JavaScript con jQuery 3.7.1** (local en `static/assets/vendor/jquery/`) para eventos, AJAX y manipulación del DOM. JS nativo solo donde jQuery no aplica bien (p. ej. clonar `<template>.content`, `scrollIntoView`). Fechas con Day.js (`Workspace.time`). Evitar dependencias y JavaScript duplicados; HTMX no se usa.
- **Estilos: Bootstrap 5.3 primero.** Usar sus componentes (card, modal, offcanvas, list-group, toast, form-control, btn, alert, spinner) y utilidades (`d-flex`, `gap-*`, `text-body-secondary`, `bg-*-subtle`…) antes de escribir CSS.
  - Colores de marca y demás valores de Bootstrap se cambian en `static/assets/css/bootstrap-theme.css` (variables `--bs-*`, sin Sass): **primario `#0066CC`**, **secundario `#F4C600`** (texto oscuro encima).
  - `static/assets/css/theme.css` solo contiene lo que Bootstrap no tiene (barra inferior, áreas seguras, accesos rápidos, avatar, movimiento) con clases `ws-*`.
- API: única raíz `/api/`; no usar `/api/v1/` ni otros prefijos de versión. Todos los endpoints están en `docs/api.md`: al agregar o cambiar uno, actualizarlo.
- Base de datos inicial: SQLite. PostgreSQL se evaluará en una etapa posterior.
- Sin Docker, React, Vue, Redis, Celery ni WebSockets en esta etapa.
- Aplicaciones propias dentro de `apps/`: `apps.accounts`, `apps.catalogs`, `apps.social`, `apps.notifications`, `apps.blog`, `apps.documents`, `apps.form_builder`, `apps.marketplace`, `apps.org`, `apps.helpdesk`.
- **Nombres que no chocan con Django/DRF:** la app de formularios es `form_builder` (no `forms`) y sus modelos `DynamicForm` (no `Form`) y `Submission` (no `Response`). El blog usa `Article` (no `Post`, que es del muro).
- Terceros: `django-allauth` (solo «Continuar con Google», limitado al dominio de la empresa; reglas en `apps/accounts/adapters.py`), `django-extensions` (`runscript`, carpeta `scripts/`), `nh3` (limpia el HTML del blog al guardar), `djangorestframework-simplejwt` (instalado, sin activar). En `static/assets/vendor/` (locales, sin CDN): jQuery, Bootstrap, Boxicons, Day.js, lottie (emojis animados), **FullCalendar 6** (calendario), **PhotoSwipe 5** (galería de las publicaciones) y **d3-org-chart 3.1.1** con d3 7.9.0 y d3-flextree 2.1.2 (organigrama, `vendor/d3-org-chart/`; sin modo compacto: en esa versión «fit» no lo cuenta). Preferir librerías mantenidas a código propio.
- `apps/core/` (paquete Python, no es app Django ni tiene modelos): utilidades compartidas. `apps/core/uploads.py` valida archivos subidos por **lista permitida y contenido real** (imágenes solo WebP decodificable; videos MP4/MOV/WebM por firma). Toda app que acepte media debe usarlo. Para documentos (tickets, documentos, formularios) usar `check_document_upload`: PDF sin contenido activo, Word/Excel/PowerPoint modernos sin macros, CSV/TXT e imágenes PNG/JPEG/WebP, máx. 20 MB.
- **Media de usuarios:** las imágenes se convierten a WebP en el navegador con `Workspace.procesarAWebP` (workspace.js) antes de subir; el servidor solo valida. Los archivos se guardan como `<id>.<ext>` y **nunca** se exponen rutas de `/media/`: se entregan por una vista que comprueba la visibilidad del objeto.
- `apps.catalogs`: **solo** datos de referencia que comparten varias apps (hoy: `Emoji` y el modelo abstracto `BaseReaction`). Lo que es de una sola app se queda en ella (p. ej. `PostCategory` en social). Se carga desde JSON en `apps/catalogs/data/` con `python manage.py load_catalogs` (idempotente, también en producción). Si tras `migrate` no hay emojis, se cargan solos (`post_migrate`).
- Archivos estáticos del proyecto dentro de `static/assets/`, organizados por tipo o función. Mantener coherencia con `STATIC_URL`, `STATICFILES_DIRS` y las rutas de las plantillas.
- La marca visible del producto es **Workspace**. Actualizar títulos, metadatos, textos, nombre de API y documentación cuando corresponda. No renombrar paquetes Python, módulos o rutas técnicas a ciegas; separar nombre comercial de identificadores internos.
- **Todas las páginas requieren sesión** (Inicio incluido; sin sesión → `/accounts/login/?next=…`), salvo Términos (`/terms/`), Privacidad (`/privacy/`) y el manifest (`/manifest.webmanifest`), que son públicos. Login con usuario **o** correo + contraseña (`apps/accounts/backends.py`) y, con credenciales, Google. No hay registro con contraseña desde la web: las cuentas sin Google las crea TI. `/admin/` sigue protegido.
- **Fechas:** el servidor usa `America/Mexico_City` (sede en Querétaro); la API manda ISO 8601 con desfase y el navegador muestra cada fecha en su propia zona.
- **Estáticos con versión:** en desarrollo `{% static %}` agrega `?v=<fecha de modificación>` (`apps/core/staticfiles.py`); en producción `ManifestStaticFilesStorage`. No poner `url(...)` de archivos inexistentes ni en comentarios CSS: `collectstatic` de producción falla.
- **Datos de prueba:** `python manage.py runscript scripts.bots.create_bots` (8 bots `bot.*` con personalidad y seguimientos, contraseña «1234») y `runscript scripts.bots.create_posts`. Personas en `scripts/bots/personas.py`. Solo corren con `DEBUG=True` (o `WORKSPACE_ALLOW_BOTS=1` a propósito). Los scripts nuevos reutilizan `scripts.bots.create_bots.get_bots()`.
- **Layout y jerarquía visual (regla):** un solo container para el encabezado y todas las páginas (`--ws-shell-width` en `theme.css`); el encabezado **nunca** cambia de ancho por página, el contenido se adapta. Páginas sin widgets (Personas, Buscar, Avisos, Calendario, secciones en construcción) usan `{% block container_class %}ws-container--fill{% endblock %}` y ocupan todo el ancho junto al menú; el perfil usa `{% block shell_class %} no-sidebar{% endblock %}` (sin menú lateral, como Facebook). Encabezado de página: `h1.h4.fw-bolder` + subtítulo `small text-body-secondary`.
- **Movimiento (guía de Emil Kowalski):** ease-out fuerte (`--ws-ease-out`), menos de 300 ms, nada animado en acciones que se usan a cada rato (cambiar de pestaña, de vista o de filtro), respuesta al presionar (`scale(.97)`), hover solo con `(hover: hover) and (pointer: fine)` y `prefers-reduced-motion` respetado.
- **Secciones en construcción** (Noticias, Documentos, Formularios, Marketplace, Ayuda, Términos, Privacidad; Calendario sin fechas): página real con el mismo encabezado y un aviso honesto. Nunca datos de prueba ni resultados falsos; lo que no existe dice «Próximamente».
- **Correo (preparado):** `apps/core/mail.py` → `send_email(to, subject, template, context)` con versión HTML y texto (`templates/emails/`, base con la marca), un correo por destinatario. Remitente `Workspace <no-reply@GOOGLE_ALLOWED_DOMAIN>` y SMTP desde `.env`; sin `EMAIL_HOST` los correos salen en la consola. La cuenta `no-reply@` aún no existe.
- **App instalable (PWA):** manifest en `/manifest.webmanifest` (`apps/core/pwa.py`, público) enlazado en `base.html` (todas las páginas), íconos del logo en `static/assets/img/icons/` (`runscript make_icons`), favicon y `apple-touch-icon`. Falta service worker.
- **API primero:** el proyecto es 100% Django, pero todo dato viaja por `/api/`; migrar a React o a una app móvil es posible sin reescribir el backend. JWT (`djangorestframework-simplejwt`) está instalado y configurado (`SIMPLE_JWT`), **sin activar**: la API usa solo sesión.

## 3. Estructura de referencia

```text
Workspace-v1/
├── manage.py · requirements.txt · .env.example · showcase.html (presentación, independiente)
├── config/
│   ├── settings/ (base.py, development.py, production.py)
│   ├── urls.py
│   └── api.py                  # raíz /api/
├── apps/
│   ├── core/                   # paquete (no app): paginación, archivos, estáticos con versión, salud, páginas generales (calendario, ayuda, legal), manifest PWA, correo
│   ├── accounts/               # User, roles/permisos, login (usuario/correo + Google), perfiles, directorio, cumpleaños
│   ├── catalogs/               # datos compartidos: Emoji, BaseReaction
│   ├── social/                 # Post, adjuntos, reacciones, comentarios, Follow
│   ├── notifications/          # Notification (avisos), PushSubscription (dispositivos para Web Push)
│   ├── blog/                   # Article, ArticleCategory, ArticleReaction, ArticleComment + API
│   ├── form_builder/           # DynamicForm, Question, QuestionOption, Submission, Answer, AnswerChoice (solo modelos)
│   ├── marketplace/            # Listing (hasta 10 fotos, vendido/disponible), ListingImage, ListingCategory + API
│   ├── org/                    # Department (subáreas, responsable) + API de departamentos y organigrama (User.manager)
│   ├── helpdesk/               # Ticket, TicketCategory, TicketComment, TicketAttachment, TicketEvent + API
│   └── documents/              # modelos, servicios y API (pantalla pendiente)
│   (cada app: models/, services/, selectors/, api/, views/, migrations/, admin.py, apps.py)
├── templates/                  # TODAS las plantillas: base.html, layouts/, pages/, components/, emails/
├── static/assets/              # css/, js/, emoji/, fonts/, img/icons/ (PWA y favicon), vendor/
├── scripts/                    # django-extensions runscript: bots/ (personas, create_bots, create_posts), fake_media.py, make_icons.py, send_test_email.py
├── tests/
└── docs/                       # api.md, architecture.md, backlog.md, media-uploads.md, reaction-emojis.md
```

Cada aplicación tiene `apps.py` con el `name` completo (`SocialConfig.name = "apps.social"`); la etiqueta sigue siendo `social`, por eso las migraciones dicen `social.Post` y no `apps.social.Post`. Las apps propias en `INSTALLED_APPS`:

```python
"apps.accounts",
"apps.catalogs",
"apps.social",
"apps.notifications",
"apps.blog",
"apps.documents",
"apps.form_builder",
"apps.marketplace",
"apps.org",
"apps.helpdesk",
```

## 4. Convenciones de código

- `models/`: modelos de datos.
- `services/`: operaciones de negocio que cambian estado o coordinan acciones.
- `selectors/`: consultas y filtros de lectura.
- `views/`: vistas HTML delgadas.
- `api/`: serializers, vistas y rutas de API organizados por responsabilidad.
- `forms/`: formularios HTML cuando se necesiten.
- Evitar archivos monolíticos y también evitar capas vacías sin necesidad.
- Las vistas HTML y la API deben compartir servicios y reglas de negocio; una vista HTML no necesita llamar por HTTP a la API de su mismo proyecto.
- Nombres de modelos descriptivos, por ejemplo `PostCategory` y `DocumentCategory`, no un `Category` ambiguo compartido entre apps.
- Mantener los secretos en `.env`, no en el repositorio.
- No afirmar que pruebas, revisiones visuales o comprobaciones se ejecutaron si no se ejecutaron.

## 5. Usuario, roles y permisos

- `accounts.User` hereda de `AbstractUser`; contempla correo único, cargo y avatar si esos campos existen en el código.
- Configurar `AUTH_USER_MODEL = "accounts.User"` antes de la primera migración si la etiqueta Django de la app sigue siendo `accounts`.
- Los roles de negocio no son departamentos ni cargos.
- Un usuario puede tener varios roles; los roles conceden permisos de negocio.
- Los permisos de negocio propios son independientes de `django.contrib.auth.Permission` y de los grupos nativos de Django.
- `/admin/` utiliza los mecanismos de Django (`is_staff`, superusuario y permisos nativos).
- Convención de códigos: `app.recurso.accion[.alcance]`, por ejemplo `social.posts.view.all`.

### `view.all`, visibilidad y permisos de modificación

- El permiso funcional determina si se puede ejecutar una acción (crear, editar, eliminar, descargar, administrar).
- `social.posts.view.all` representa el alcance de consulta de todas las publicaciones, incluso las que no aparecen por las reglas normales de audiencia. No concede edición, borrado, descarga ni administración.
- Sin `view.all`, los selectores deben aplicar en el servidor la visibilidad correspondiente.
- No confiar en ocultar botones en el frontend como medida de seguridad.
- El acceso a un objeto por URL o ID también debe validar permisos y visibilidad.
- `view.all` no elimina requisitos generales de autenticación, CSRF ni otras medidas de seguridad cuando sean aplicables.

## 6. Arquitectura de frontend: mobile-first Workspace

### Enfoque

Diseñar primero para teléfonos y tabletas pequeñas, y ampliar de forma progresiva para escritorio. El resultado debe parecer una aplicación de trabajo moderna, no una web de escritorio encogida ni un clon de Facebook.

La referencia visual puede describirse como **mobile-first app UI**, **soft UI** o **card-based dashboard UI**: superficies claras, tarjetas redondeadas, sombra discreta, iconografía consistente, acentos de marca (azul primario, amarillo secundario) y navegación inferior. No usar neomorfismo extremo ni sombras que reduzcan el contraste.

### Navegación principal: 4 o 5 destinos

No incluir “Perfil” ni “Favoritos” como destinos principales. Propuesta inicial de cinco:

1. **Inicio** — feed de novedades internas, avisos recientes y accesos rápidos.
2. **Avisos** — anuncios institucionales y notificaciones relevantes; separar avisos oficiales de notificaciones personales si la funcionalidad lo requiere.
3. **Documentos** — biblioteca de documentos y recursos internos.
4. **Formularios** — formularios disponibles y, más adelante, estado de envíos.
5. **Menú** — entrada a otras aplicaciones y recursos de la intranet, categorías, ayuda y opciones adicionales.

Si cinco elementos quedan demasiado apretados en dispositivos muy estrechos, usar cuatro destinos visibles (`Inicio`, `Avisos`, `Documentos`, `Menú`) y colocar `Formularios` dentro de Menú. La decisión debe comprobarse visualmente en el ancho mínimo acordado.

### Navegación vigente (implementada)

- **Encabezado** (mismo container en todas las páginas): logo (→ Inicio), campana (→ Avisos) y «Mi cuenta» (avatar; con nombre en escritorio) con un menú desplegable de Bootstrap: Ver mi perfil · Ayuda · Cerrar sesión. En teléfono/tablet, además, el botón del menú.
- **Barra inferior (teléfono):** Inicio · Avisos · Buscar · Más (abre el menú). Las tres primeras son páginas; `active_nav` marca la actual y coloca el indicador.
- **Menú lateral** (columna fija ≥ 992px; panel en teléfono): *Principal* → Inicio, Avisos, Buscar, Calendario, Noticias, Documentos, Formularios, Marketplace, Personas, Perfil · *Cuenta* → Ayuda, Cerrar sesión · pie pequeño con Términos, Privacidad y ©. Ya no hay tarjeta de perfil en el menú (está en el encabezado).
- Buscar dejó de ser una vista de la portada (`#buscar`): es la página `/search/`. Los enlaces viejos `/#buscar` y `/#avisos` redirigen a sus páginas.

### Barra inferior y área visible

- La barra inferior debe ser fija o sticky en la ventana de la aplicación, con icono y etiqueta para cada destino.
- Contemplar `env(safe-area-inset-bottom)` para dispositivos con zonas seguras.
- Añadir `padding-bottom` al contenido para que la barra no tape el último elemento.
- La interfaz se adapta a la altura/ancho reales del viewport y a la barra del navegador; no asumir que el navegador inferior siempre está visible o siempre tiene la misma altura.
- No usar alturas rígidas que dependan de un modelo de teléfono concreto.
- Utilizar unidades modernas como `100dvh` con fallback razonable, y probar en navegadores móviles.
- Las medidas personalizadas del producto se definirán en `static/assets/css/theme.css` mediante variables `--ws-*`; no depender exclusivamente de los breakpoints predeterminados de Bootstrap.
- Se pueden usar media queries propias, documentadas y orientadas al contenido, por ejemplo para móvil estrecho, tablet pequeña y escritorio. No asumir que “iPad mini” tiene siempre un único viewport CSS.
- El área central debe desplazarse sin mover innecesariamente la navegación principal.

### Sistema visual

Definir variables centralizadas `--ws-*` en `static/assets/css/theme.css` para:
- colores de marca, fondos, superficies, texto y estados;
- tipografía, tamaños y alturas de línea;
- radios, sombras y bordes;
- espacios, ancho máximo y separación entre tarjetas;
- altura y espaciado de navegación;
- puntos de ruptura propios;
- transiciones y foco accesible.

Dirección visual recomendada:
- Fondo general gris-lavanda muy claro o neutro.
- Superficies blancas, bordes sutiles y radios amplios pero consistentes.
- Azul `#0066CC` (primario) para botones, iconos activos y acciones principales; amarillo `#F4C600` (secundario) con moderación para destacar. Definidos en `bootstrap-theme.css`.
- Tipografía legible, títulos compactos y metadatos secundarios con contraste suficiente.
- Iconos de una misma familia, idealmente Bootstrap Icons si ya está cargada.
- Tarjetas con jerarquía clara; evitar convertir cada línea en una tarjeta independiente.
- Animaciones discretas y respetar `prefers-reduced-motion`.
- Estados vacíos, carga, error y confirmación diseñados desde el inicio.
- Contraste, foco de teclado, etiquetas accesibles y áreas táctiles cómodas.

### Inicio y feed

El Inicio es una mesa de trabajo, no un muro social recreativo:
- Encabezado compacto con marca Workspace y acceso a avisos.
- Saludo opcional, solo si existe un usuario o contexto apropiado; no inventar una identidad real en producción.
- Accesos rápidos a Documentos, Formularios y Menú según el diseño.
- Sección de avisos importantes con jerarquía visual diferenciada.
- Feed de novedades internas con texto, fecha, autor/área cuando existan, adjuntos y acciones autorizadas.
- Datos de demostración claramente identificados como tales.
- No usar favoritos ni perfil como elementos de navegación primaria.
- En escritorio, aprovechar el ancho con una columna central legible y paneles laterales solo cuando aporten valor; no estirar el texto a todo el ancho.

### Breakpoints y medidas

No tomar los breakpoints de Bootstrap como especificación de diseño. Definir breakpoints propios en CSS según las pruebas visuales y el contenido real. Como punto de partida (ajustable tras probar):
- móvil estrecho: hasta `359px`;
- móvil: `360px–599px`;
- tablet pequeña: `600px–899px`;
- escritorio: `900px` en adelante.

Estos valores son una hipótesis inicial de diseño, no reglas universales de dispositivos. La navegación debe funcionar en todos los anchos, incluidos zoom y texto grande.


## 6.1 Arquitectura de templates y componentes reutilizables

Usar una arquitectura de **Django Templates por layouts, páginas, secciones y componentes**. Django no necesita un framework SPA para reutilizar HTML: la reutilización se hace con herencia de templates e inclusiones parciales.

Estructura recomendada:

```text
templates/
├── base.html                     # Documento HTML base: head, assets y bloques globales
├── layouts/
│   ├── app.html                  # Layout de la aplicación con navegación principal
│   └── public.html               # Layout para páginas públicas puntuales, si se necesita
├── pages/
│   ├── home/
│   │   └── index.html
│   ├── notices/
│   │   ├── index.html
│   │   └── detail.html
│   ├── documents/
│   │   ├── index.html
│   │   └── detail.html
│   ├── forms/
│   │   ├── index.html
│   │   └── detail.html
│   └── errors/
│       ├── 403.html
│       ├── 404.html
│       └── 500.html
├── components/
│   ├── navigation/
│   │   ├── bottom_nav.html
│   │   ├── top_bar.html
│   │   └── menu_drawer.html
│   ├── posts/
│   │   ├── post_card.html
│   │   ├── post_header.html
│   │   ├── post_content.html
│   │   ├── post_attachments.html
│   │   └── post_actions.html
│   ├── notices/
│   │   └── notice_card.html
│   ├── documents/
│   │   └── document_card.html
│   ├── forms/
│   │   └── form_card.html
│   ├── feedback/
│   │   ├── empty_state.html
│   │   ├── loading.html
│   │   └── pagination.html
│   └── ui/
│       ├── avatar.html
│       ├── icon_button.html
│       ├── badge.html
│       └── section_header.html
└── emails/                       # Plantillas de correo, si se incorporan
```

Esta estructura es una guía funcional; no es necesario crear cada archivo hasta que se utilice.

### Responsabilidad de cada nivel

- `base.html`: etiquetas HTML globales, metadatos, carga de CSS/JS compartidos y bloques como `title`, `extra_css`, `content` y `extra_js`. No debe contener el contenido específico de una página.
- `layouts/`: arman una composición general reutilizable. `layouts/app.html` extiende `base.html` e incluye cabecera, navegación inferior y contenedor de contenido.
- `pages/`: una plantilla por página/ruta o pantalla. Define el contenido de esa pantalla y extiende un layout.
- `components/`: piezas pequeñas reutilizables con una responsabilidad clara, incluidas con `{% include %}`.
- `sections/`: usar solo cuando una sección completa de una página se reutilice o tenga suficiente complejidad. No crear una carpeta `sections/` por obligación; las secciones específicas de una página pueden permanecer dentro de su template de página.

### Ejemplo: una tarjeta de publicación compartida

El mismo componente `components/posts/post_card.html` debe usarse en Inicio, búsquedas, páginas de área o cualquier futura página que muestre publicaciones. No duplicar el HTML de la tarjeta en cada pantalla.

```django
{# pages/home/index.html #}
{% extends "layouts/app.html" %}

{% block content %}
  <section class="ws-feed" aria-label="Novedades">
    {% for post in posts %}
      {% include "components/posts/post_card.html" with post=post only %}
    {% empty %}
      {% include "components/feedback/empty_state.html" with title="Todavía no hay novedades" description="Cuando se publiquen novedades aparecerán aquí." only %}
    {% endfor %}
  </section>
{% endblock %}
```

El componente `post_card.html` recibe un objeto `post` y muestra su estructura común. Si hay variaciones reales, pásalas mediante variables explícitas como `show_area=True` o `compact=True`; evita que el componente dependa de variables globales misteriosas.

```django
{# components/posts/post_card.html #}
<article class="ws-post-card">
  <header class="ws-post-card__header">
    {% include "components/ui/avatar.html" with user=post.author only %}
    <div class="ws-post-card__author">
      <strong>{{ post.author.get_full_name|default:post.author.username }}</strong>
      <time datetime="{{ post.created_at|date:'c' }}">{{ post.created_at|date:"d M Y, H:i" }}</time>
    </div>
  </header>

  <div class="ws-post-card__body">
    {{ post.content|linebreaksbr }}
  </div>

  {% if post.attachments.all %}
    {% include "components/posts/post_attachments.html" with post=post only %}
  {% endif %}

  {% include "components/posts/post_actions.html" with post=post only %}
</article>
```

Este código es ilustrativo: ajustar los nombres de campos y relaciones a los modelos reales, optimizar las consultas (`select_related`/`prefetch_related`) y no asumir que `post.attachments.all` evita consultas adicionales. La plantilla no debe implementar autorización ni decidir por sí sola si una publicación puede ser vista.

### Reglas para componentes

1. Reutiliza un componente cuando represente el mismo concepto y estructura en más de un lugar.
2. Mantén componentes pequeños, pero no conviertas cada etiqueta HTML en un archivo separado.
3. Pasa datos explícitamente con `with ... only` cuando sea viable para reducir dependencias implícitas.
4. La lógica de negocio, autorización, filtrado de audiencia y consultas pertenece al backend, no al template.
5. No copies la tarjeta para cambiar solo el color: usa modificadores CSS como `.ws-post-card--compact` o una variable explícita.
6. Los componentes deben tener clases CSS estables con prefijo `ws-`; no depender de selectores HTML frágiles.
7. Las interacciones compartidas pueden tener JS en `static/assets/js/components/` o en un módulo común, pero no cargar el mismo script repetidamente en cada include.
8. La paginación, estados vacíos, avisos y tarjetas deben mantener accesibilidad y funcionar sin JavaScript siempre que sea razonable.

### Herencia de templates

```django
{# base.html #}
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Workspace{% endblock %}</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'assets/css/theme.css' %}">
  {% block extra_css %}{% endblock %}
</head>
<body>
  {% block app_shell %}{% endblock %}
  <script src="{% static 'assets/js/workspace.js' %}" defer></script>
  {% block extra_js %}{% endblock %}
</body>
</html>
```

```django
{# layouts/app.html #}
{% extends "base.html" %}

{% block app_shell %}
  <div class="ws-app">
    {% include "components/navigation/top_bar.html" %}
    <main id="main-content" class="ws-main">
      {% block content %}{% endblock %}
    </main>
    {% include "components/navigation/bottom_nav.html" %}
  </div>
{% endblock %}
```

Los nombres de bloques se pueden ajustar a la estructura existente. No sustituir plantillas funcionales sin revisar primero las vistas y los templates actuales.

## 6.2 Templates centralizados y frontend por API

- **Todas las plantillas viven en `templates/` (raíz).** No crear `apps/<app>/templates/`. `APP_DIRS` sigue activo solo para plantillas de terceros (admin, DRF).
- **Los datos se consumen por API**, no renderizados por Django ni con respuestas AJAX internas que devuelvan HTML. Las páginas Django son un *shell* (layout, navegación, `<template>` de componentes); el JS pide JSON a `/api/...` y pinta. Así el frontend podrá migrarse a React u otro framework sin tocar el backend.
- Cada endpoint nuevo se documenta en `docs/api.md` (método, ruta, cuerpo y respuesta).
- Las reacciones usarán emojis animados (Noto) definidos en un catálogo JSON; la lista la da el responsable del proyecto, no inventarla (ver `docs/reaction-emojis.md`).

## 7. Dependencias de frontend

Antes de agregar o cambiar bibliotecas, revisa `templates/base.html` y `requirements.txt`. Evitar duplicados. Las bibliotecas CDN existentes en la documentación original deben confirmarse contra el código real antes de dar por hecho que siguen cargadas. Bootstrap se usa como apoyo, no como sistema de diseño rígido. DataTables solo debe añadirse cuando exista una tabla real que lo necesite; para listas grandes, usar procesamiento del lado servidor.

## 8. Datos estáticos y media

- Los recursos estáticos propios se organizan en `static/assets/` (por ejemplo `css/theme.css`, `js/workspace.js`, `img/` y `vendor/`).
- Actualizar referencias de plantillas y configuración para que apunten a las ubicaciones reales.
- En Django, usar `{% load static %}` y `{% static 'assets/css/theme.css' %}` si `static/` es la raíz configurada.
- Los archivos subidos por usuarios (avatares, documentos y adjuntos) son `MEDIA`, no `static`. En producción, definir controles de acceso y almacenamiento adecuados.
- No colocar archivos privados de empleados dentro de una ruta estática pública.

## 9. Base de datos y migraciones

- Base inicial: SQLite, normalmente `db.sqlite3`, excluida de Git.
- Configuración por variables de entorno si ya está implementada.
- Antes de `migrate`, verificar `AUTH_USER_MODEL`, `INSTALLED_APPS`, `apps.py`, importaciones de modelos y migraciones iniciales.
- Una vez aplicada una migración compartida o con datos, no borrarla por rutina; crear migraciones nuevas.
- PostgreSQL será una etapa posterior: revisar tipos, restricciones, índices, consultas, migraciones, transferencia y pruebas de integridad. No asumir que cambiar variables migra datos.

## 10. Etapas y checklist

El avance real (hecho / pendiente / por decidir) vive en **`docs/backlog.md`** y se actualiza al cerrar cada tanda; no duplicar listas aquí. Orden general: social y avisos (hecho) → pantallas grandes y navegación (hecho) → páginas de todas las secciones (hechas; varias en construcción) → interfaz de blog, formularios y marketplace (modelos/API listos) → documentos → correo y PWA completos → PostgreSQL → producción.

## 11. Reglas de trabajo para agentes

**Backlog:** lo pendiente vive en `docs/backlog.md`. Se trabaja por tandas: al terminar una tanda, actualizar ese archivo (marcar lo hecho, agregar lo nuevo). Cuando el responsable pregunte qué falta, responder desde ahí.

1. Inspecciona los archivos reales antes de cambiar.
2. No renombres paquetes, apps, modelos ni rutas por coincidencia de marca sin revisar dependencias.
3. No ejecutes migraciones destructivas ni borres migraciones sin explicar consecuencias.
4. No habilites acceso público a `/admin/` ni a operaciones sensibles.
5. No inventes resultados de pruebas.
6. Cambia documentación junto con el código cuando las decisiones cambien.
7. Trabaja por pasos pequeños y termina cada paso con archivos modificados, comandos ejecutados y pendientes conocidos.
