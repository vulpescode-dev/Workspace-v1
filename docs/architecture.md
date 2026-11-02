# Arquitectura de Workspace

**Propósito:** describir la arquitectura del producto y las decisiones que debe seguir el código. El estado exacto de implementación se debe comprobar en el repositorio; esta documentación no sustituye las pruebas ni una inspección del código.

## 1. Producto y principios
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



Workspace es una intranet empresarial y mesa de trabajo digital, no una red social pública. El diseño permite consultar novedades, avisos, documentos y formularios desde dispositivos móviles, tabletas pequeñas y escritorio.

Principios:
- Monolito modular de Django.
- Separación entre modelos, consultas, lógica de negocio, vistas y API.
- Reglas de autorización en servidor.
- Diseño mobile-first con sistema visual propio.
- Accesibilidad, legibilidad y rendimiento antes que efectos decorativos.
- Evolución por etapas, sin introducir infraestructura antes de necesitarla.

## 2. Stack

- Django 5.2 LTS.
- Django REST Framework.
- Django Templates.
- HTML, CSS y JavaScript.
- Bootstrap 5.3 como base (componentes y utilidades), con tema propio en `static/assets/css/bootstrap-theme.css` (primario `#0066CC`, secundario `#F4C600`). `theme.css` solo para lo que Bootstrap no cubre.
- jQuery 3.7.1 (local) para la mayor parte del JS; JS nativo solo donde jQuery no aplica (clonar `<template>`). Day.js para fechas.
- SQLite al inicio; PostgreSQL en una etapa posterior.
- django-allauth (solo Google, dominio de la empresa), django-extensions (`runscript`), nh3 (HTML del blog), djangorestframework-simplejwt (instalado, sin activar).
- Librerías de frontend locales en `static/assets/vendor/`: lottie (emojis animados), FullCalendar 6 (calendario), PhotoSwipe 5 (galería de las publicaciones).
- Correo con el sistema de Django (`apps/core/mail.py`); SMTP desde `.env` cuando exista la cuenta `no-reply@`.
- Sin Docker, React, Vue, Redis, Celery ni WebSockets en la etapa actual.

La raíz de API es `/api/`. No crear `/api/v1/`.

## 3. Estructura del repositorio

```text
Workspace-v1/
├── manage.py · requirements.txt · .env.example · showcase.html (presentación, independiente)
├── config/
│   ├── settings/ (base.py, development.py, production.py)
│   ├── urls.py
│   └── api.py                  # raíz /api/
├── apps/
│   ├── core/                   # paquete (no app): paginación, validación de archivos, estáticos con versión
│   ├── accounts/               # User, roles/permisos, login (usuario/correo + Google), perfiles, directorio, cumpleaños
│   ├── catalogs/               # datos compartidos: Emoji, BaseReaction
│   ├── social/                 # Post, adjuntos, reacciones, comentarios, Follow
│   ├── notifications/          # Notification (avisos)
│   ├── blog/                   # Article, ArticleCategory, ArticleReaction, ArticleComment (solo modelos)
│   ├── form_builder/           # DynamicForm, Question, QuestionOption, Submission, Answer, AnswerChoice (solo modelos)
│   └── documents/              # modelos, servicios y API (pantalla pendiente)
│   (cada app: models/, services/, selectors/, api/, views/, migrations/, admin.py, apps.py)
├── templates/                  # TODAS las plantillas: base.html, layouts/, pages/, components/
├── static/assets/              # css/, js/, emoji/, fonts/, vendor/
├── scripts/                    # django-extensions runscript: bots/ (personas, create_bots, create_posts), fake_media.py
├── tests/
└── docs/                       # architecture.md, backlog.md, media-uploads.md, reaction-emojis.md
```

### Configuración de apps en `apps/`

`INSTALLED_APPS` incluye, además de Django, DRF, django-extensions y allauth:

```python
"apps.accounts",
"apps.catalogs",
"apps.social",
"apps.notifications",
"apps.blog",
"apps.documents",
"apps.form_builder",
```

Cada `apps.py` usa el paquete Python completo (`name = "apps.social"`). La etiqueta de la app (`social`) es la que aparece en migraciones (`social.Post`); no convertirla a `apps.social.Post`. `AUTH_USER_MODEL = "accounts.User"`.

## 4. Responsabilidad de cada aplicación

| Aplicación | Responsabilidad | Estado |
|---|---|---|
| `apps.accounts` | Usuario, roles y permisos de negocio, login (usuario/correo y Google), perfiles, directorio, cumpleaños. | Implementado y probado. |
| `apps.social` | Publicaciones, adjuntos (fotos/videos), reacciones, comentarios, seguidores y audiencias. | Implementado y probado. |
| `apps.notifications` | Avisos (`Notification`: título, descripción, ícono, color, fecha, enlace). | Tabla, API y página; aún no se generan solos. |
| `apps.catalogs` | Datos compartidos entre apps: `Emoji` (reacciones) y `BaseReaction`. | Implementado y probado. |
| `apps.blog` | Noticias: `Article` (HTML limpiado con nh3), `ArticleCategory`, `ArticleReaction`, `ArticleComment`. | Modelos, admin y API (`/api/blog/`); página `/blog/` en construcción. |
| `apps.form_builder` | Formularios estilo Google Forms: `DynamicForm`, `Question` (texto, opción única, casillas, desplegable, escala, calificación, cuadrículas, fecha, hora), `QuestionOption` (opciones y filas de cuadrícula; se archivan, no se borran), `Submission`, `Answer` y `AnswerChoice` (una fila por opción elegida, lista para contar por opción). | Solo modelos y admin; página `/forms/` en construcción. |
| `apps.documents` | Biblioteca documental y descargas autorizadas. | Pendiente; página `/documents/` en construcción. |
| `apps.marketplace` | Compra-venta entre compañeros: `Listing`, `ListingImage`, `ListingCategory`. | Modelos, admin y API (`/api/marketplace/`); página `/marketplace/` en construcción. |
| `apps.org` | Estructura: `Department` (subáreas con `parent`, responsable `head`). El departamento y el jefe directo de cada persona están en `User.department` / `User.manager` hasta que exista la tabla de empleados. | Modelo, admin y API (`/api/org/`: departamentos y organigrama). |
| `apps.helpdesk` | Mesa de ayuda: `TicketCategory` (qué departamento atiende), `Ticket`, `TicketComment` (públicos e internos), `TicketAttachment`, `TicketEvent` (historial). | Modelos, servicios, admin y API (`/api/helpdesk/`); página `/helpdesk/` en construcción. |

## 5. Organización interna

Usar las siguientes capas cuando exista una responsabilidad concreta:

- `models/`: estructura y reglas locales de datos.
- `services/`: operaciones de negocio que cambian estado o coordinan varios modelos.
- `selectors/`: consultas de lectura, filtros de visibilidad y optimización de querysets.
- `views/`: controladores HTML delgados.
- `api/`: endpoints, serializers y validación de entrada para DRF.
- `forms/`: formularios HTML si hacen falta.
- `admin.py`: configuración del Django Admin.

La vista HTML y la API deben reutilizar servicios y reglas de negocio. Una plantilla no tiene que consumir su propia API mediante una petición HTTP. Evitar tanto las vistas con demasiada lógica como las capas vacías creadas solo por cumplir una estructura.

Usar nombres de modelo específicos: `PostCategory`, `DocumentCategory`, etc. No compartir una clase genérica `Category` entre dominios distintos sin una razón clara.

## 6. Cuentas, roles y permisos

Modelo conceptual:

```text
User ──< UserRole >── Role ──< RolePermission >── Permission
```

- `User` hereda de `AbstractUser`; los campos adicionales pueden incluir email único, cargo y avatar.
- Un usuario puede tener varios roles.
- Los roles representan responsabilidades de Workspace; no son departamentos ni cargos.
- Los permisos de negocio se mantienen separados de los permisos nativos de Django.
- `/admin/` sigue usando el sistema nativo de Django, incluyendo `is_staff` y superusuario.

Convención de permisos:

`app.recurso.accion[.alcance]`

Ejemplo: `social.posts.view.all`.

### Diferencias de autorización

1. **Permiso funcional:** permite una acción concreta, como crear, editar, eliminar o descargar.
2. **Alcance `view.all`:** permite consultar todos los registros del recurso aunque la audiencia normalmente los excluya. No concede modificación ni administración.
3. **Visibilidad:** determina qué registros puede ver normalmente la persona, según las reglas del recurso.

Los selectores del servidor deben aplicar las reglas de visibilidad. Nunca basta con ocultar botones. Las vistas de detalle, las API y las descargas también deben validar el acceso al objeto.

## 7. Acceso y administración

- **Todo requiere sesión**, incluida la portada (sin sesión → `/accounts/login/?next=…`). Públicos: `/terms/`, `/privacy/` (se enlazan desde el login) y `/manifest.webmanifest` (el navegador lo pide sin cookies).
- Login: un campo «Usuario o correo» + contraseña (`apps/accounts/backends.py`, `UsernameOrEmailBackend`); el error es genérico y no revela qué cuentas existen.
- «Continuar con Google» (django-allauth): solo cuentas del Workspace de la empresa (`GOOGLE_ALLOWED_DOMAIN`), validado en el servidor (`apps/accounts/adapters.py`). Primera vez = cuenta creada; mismo correo = cuenta vinculada (su contraseña local se desactiva por seguridad). Sin credenciales en `.env`, el botón sale deshabilitado en desarrollo y oculto en producción. De allauth solo se exponen las rutas de Google; registro, recuperar contraseña, etc. redirigen al login.
- `/admin/` protegido por Django. Cargo, área y fecha de nacimiento los edita RRHH/TI ahí.
- Bots de desarrollo (`scripts/bots/`) con contraseña «1234»: los scripts se niegan a correr con `DEBUG=False` (salvo `WORKSPACE_ALLOW_BOTS=1` explícito).

## 8. Frontend: sistema visual mobile-first

### Nombre del patrón visual

La referencia se aproxima a una **interfaz de aplicación móvil basada en tarjetas (card-based mobile app UI)**, con rasgos de **soft UI**: fondos claros, tarjetas blancas, esquinas redondeadas, sombras suaves, iconos lineales y acentos de marca (azul `#0066CC`, amarillo `#F4C600`). No se busca replicar una app de reservas; se toma su lenguaje visual para una intranet de trabajo.

### Diseño de navegación

Propuesta inicial de cinco destinos:

1. Inicio.
2. Avisos.
3. Documentos.
4. Formularios.
5. Menú.

En móviles muy estrechos, puede reducirse a cuatro destinos visibles (`Inicio`, `Avisos`, `Documentos`, `Menú`) y situar `Formularios` dentro de Menú. No colocar `Perfil` ni `Favoritos` en la navegación principal.

La barra inferior debe:
- incluir icono y etiqueta;
- indicar claramente el destino activo;
- mantenerse accesible al desplazarse;
- respetar `safe-area-inset-bottom`;
- no tapar el contenido;
- tener áreas táctiles cómodas y estados de foco accesibles.

### Navegación vigente (implementada)

- **Encabezado** (mismo container en todas las páginas): logo (→ Inicio), campana (→ Avisos) y «Mi cuenta» (avatar; con nombre en escritorio) con un menú desplegable de Bootstrap: Ver mi perfil · Ayuda · Cerrar sesión. En teléfono/tablet, además, el botón del menú.
- **Barra inferior (teléfono):** Inicio · Avisos · Buscar · Más (abre el menú). Las tres primeras son páginas; `active_nav` marca la actual y coloca el indicador.
- **Menú lateral** (columna fija ≥ 992px; panel en teléfono): *Principal* → Inicio, Avisos, Buscar, Calendario, Noticias, Documentos, Formularios, Marketplace, Personas, Perfil · *Cuenta* → Ayuda, Cerrar sesión · pie pequeño con Términos, Privacidad y ©. Ya no hay tarjeta de perfil en el menú (está en el encabezado).
- Buscar dejó de ser una vista de la portada (`#buscar`): es la página `/search/`. Los enlaces viejos `/#buscar` y `/#avisos` redirigen a sus páginas.

### Vista Inicio

La pantalla principal debe sentirse como una mesa de trabajo:
- encabezado compacto con marca Workspace;
- avisos prioritarios y novedades recientes;
- accesos rápidos a funciones frecuentes;
- feed interno con texto, área/autora, fecha y adjuntos cuando existan;
- tarjetas informativas con jerarquía clara;
- estado vacío útil y contenido de demostración claramente marcado.

Evitar patrones propios de una red social recreativa como perfiles destacados o favoritos como eje principal. Comentarios y reacciones pueden existir como herramientas de colaboración, pero no deben dominar visualmente la interfaz.

### CSS y medidas personalizadas

El sistema de diseño se centraliza en `static/assets/css/theme.css` con variables `--ws-*`. Como mínimo, centralizar:
- paleta, texto y superficies;
- tipografía y tamaños;
- espaciado;
- radios, bordes y sombras;
- ancho máximo de lectura;
- dimensiones de navegación;
- breakpoints propios;
- transiciones y estados de interacción.

No depender únicamente de los breakpoints de Bootstrap. Valores iniciales para pruebas, no reglas de dispositivo definitivas:

- hasta `359px`: móvil estrecho;
- `360px–599px`: móvil;
- `600px–899px`: tablet pequeña;
- `900px` en adelante: escritorio.

Ajustar estos valores al probar el contenido. Considerar zoom, texto grande y orientación horizontal.

No fijar la altura del contenido según una altura universal del navegador móvil: las barras de navegación del navegador cambian entre dispositivos y estados. Usar unidades como `100dvh` con fallback apropiado cuando sea necesario, `env(safe-area-inset-bottom)` y padding inferior para la barra propia de la aplicación.

### Dirección visual

- Fondo general neutro claro o lavanda muy tenue.
- Tarjetas blancas con radios consistentes y sombra ligera.
- Azul `#0066CC` para acciones principales e iconos activos; amarillo `#F4C600` como acento secundario.
- Texto principal oscuro y metadatos con contraste suficiente.
- Iconografía de una sola familia.
- Animaciones discretas; respetar `prefers-reduced-motion`.
- Diseñar estados de carga, error, vacío y confirmación.
- En escritorio, limitar el ancho del contenido y añadir paneles secundarios solo si ayudan a trabajar.


## 8.1 Arquitectura de templates y reutilización

El frontend debe organizarse como **Django Templates con herencia de layouts y componentes parciales**. Esto permite compartir tarjetas, cabeceras, navegación, estados vacíos y acciones sin introducir React/Vue.

Estructura objetivo:

```text
templates/
├── base.html
├── layouts/
│   ├── app.html
│   └── public.html
├── pages/
│   ├── home/index.html
│   ├── notices/index.html
│   ├── notices/detail.html
│   ├── documents/index.html
│   ├── documents/detail.html
│   ├── forms/index.html
│   ├── forms/detail.html
│   └── errors/{403,404,500}.html
├── components/
│   ├── navigation/{top_bar,bottom_nav,menu_drawer}.html
│   ├── posts/{post_card,post_header,post_content,post_attachments,post_actions}.html
│   ├── notices/notice_card.html
│   ├── documents/document_card.html
│   ├── forms/form_card.html
│   ├── feedback/{empty_state,loading,pagination}.html
│   └── ui/{avatar,icon_button,badge,section_header}.html
└── emails/
```

Es una estructura objetivo, no una lista de archivos que deban crearse todos desde el primer día.

- **`base.html`:** estructura HTML global, metadatos, CSS/JS compartidos y bloques.
- **`layouts/`:** composición de la aplicación. `app.html` incluye encabezado, área principal y navegación inferior.
- **`pages/`:** contenido específico de cada pantalla.
- **`components/`:** elementos reutilizables incluidos con `{% include %}`.
- **`sections/`:** carpeta opcional; solo crearla si existen secciones completas que se reutilizan o tienen suficiente complejidad. No es obligatoria.

### Una tarjeta de publicación para todos los lugares

`components/posts/post_card.html` es la representación compartida de una publicación. Inicio, resultados de búsqueda y futuras páginas de área deben incluir el mismo componente en vez de copiar el markup.

Ejemplo:

```django
{% for post in posts %}
  {% include "components/posts/post_card.html" with post=post only %}
{% empty %}
  {% include "components/feedback/empty_state.html" with title="Todavía no hay novedades" only %}
{% endfor %}
```

Si una tarjeta necesita variantes, pásalas explícitamente (`compact=True`, `show_area=True`) y usa modificadores CSS como `.ws-post-card--compact`; no mantengas copias independientes para cada página. El componente debe recibir los datos que necesita y no ejecutar lógica de autorización. La vista o selector del backend decide qué publicaciones son visibles.

### Ejemplo de layout

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

### Reglas

1. Reutilizar componentes para conceptos compartidos: tarjeta de publicación, avatar, adjuntos, navegación, aviso, tarjeta de documento, paginación y estados vacíos.
2. Evitar fragmentar tanto que cada etiqueta HTML sea su propio archivo.
3. Preferir variables explícitas y `{% include ... with ... only %}` para reducir dependencias ocultas.
4. Mantener clases CSS propias con prefijo `ws-`.
5. Cargar scripts compartidos una sola vez; los includes no deben repetir `<script>` por cada tarjeta.
6. Mantener lógica de negocio, consultas, visibilidad y permisos en Python.
7. Si una tarjeta incluye relaciones (autor, adjuntos, reacciones), optimizar el queryset con `select_related` y `prefetch_related` según los campos reales.
8. El HTML de la tarjeta debe ser común; la apariencia variable se resuelve con modificadores CSS y datos explícitos.

La estructura se implementa gradualmente. Antes de mover o renombrar templates existentes, comprobar las rutas de las vistas y las referencias `{% extends %}` y `{% include %}`.

## 9. Estáticos y archivos subidos

Los archivos estáticos propios se organizan en `static/assets/`, por ejemplo:

- `static/assets/css/theme.css`
- `static/assets/js/workspace.js`
- `static/assets/img/`
- `static/assets/vendor/`

Si `static/` es la raíz estática configurada, las plantillas pueden referenciar el tema con:

```django
{% load static %}
<link rel="stylesheet" href="{% static 'assets/css/theme.css' %}">
```

Confirmar `STATIC_URL`, `STATICFILES_DIRS` y el uso de `{% load static %}` en el proyecto real.

No guardar documentos internos o archivos privados subidos por empleados dentro de `static/`. Los uploads corresponden a `MEDIA` y necesitan validación, autorización de descarga y almacenamiento adecuado.

## 10. API

- Raíz única: `/api/`.
- No versionar la ruta como `/api/v1/`.
- La API debe reutilizar las reglas de negocio y autorización de la aplicación.
- Los endpoints deben documentarse cuando se implementen.
- No declarar endpoints funcionales si solo existe un endpoint informativo o de estado.

## 11. Base de datos y migraciones

SQLite es la base inicial. Django crea el archivo configurado al aplicar `migrate`.

Antes de la primera migración:
1. confirmar `AUTH_USER_MODEL`;
2. revisar `INSTALLED_APPS` y `AppConfig.name`;
3. confirmar que los modelos de módulos separados se importen;
4. comprobar las migraciones iniciales;
5. ejecutar `python manage.py check`.

No borrar una migración solo porque todavía no existe la base de datos. Si los modelos cambian, generar migraciones nuevas según el estado del proyecto. PostgreSQL se abordará en una etapa posterior con pruebas de transferencia e integridad.

## 12. Comandos de desarrollo

Instalación y uso paso a paso (Windows y macOS) en el `README.md`. Con el entorno activo:

```bash
python manage.py migrate                  # crea/actualiza la BD (y carga los emojis)
python manage.py runserver                # http://localhost:8000/
python manage.py test tests               # pruebas
python manage.py runscript scripts.bots.create_bots    # 8 bots de prueba y sus seguimientos (contraseña «1234»)
python manage.py runscript scripts.bots.create_posts   # 24 publicaciones de los bots (--script-args N)
python manage.py load_catalogs            # tras editar apps/catalogs/data/emojis.json
python manage.py makemigrations           # tras cambiar modelos
python manage.py runscript make_icons     # regenera íconos PWA/favicon (solo si cambia el logo)
python manage.py runscript send_test_email --script-args tu@correo.com   # correo de prueba con la plantilla
python manage.py sendtestemail tu@correo.com                              # prueba la conexión SMTP (Django)
```

## 13. Etapas de desarrollo

Ver `docs/backlog.md` (se trabaja por tandas y ahí se marca lo hecho y lo pendiente).

## 14. Estado de implementación

Esta sección debe actualizarse después de revisar el repositorio y ejecutar comprobaciones. Distinguir claramente:
- implementado y probado;
- implementado pero no probado;
- estructura creada, sin funcionalidad;
- planeado para una etapa futura.

No conservar cifras antiguas de pruebas o afirmaciones sobre el estado si no se han vuelto a verificar.

### Actualización: social reiniciado — publicaciones de texto por API

- **Reinicio de `apps.social`:** se eliminaron `PostCategory`, `PostAudience`, `PostAttachment`, `PostReaction`, `PostComment` y `CommentReaction`, y su migración. Se reconstruye poco a poco; las migraciones se limpiarán al final de la etapa.
- **Implementado y probado:** modelo `Post` (autor, texto, fechas), servicio `services/posts.create_post`, selector `selectors/posts.visible_posts` (persona autenticada y activa ve todo; anónimo nada) y API:

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/social/posts/` | Lista paginada (25, o menos con `?page_size=`), más recientes primero. El feed pide 5 para el scroll infinito. |
| POST | `/api/social/posts/` | Crea una publicación. JSON `{"body"}` o multipart con `body` y uno o varios `files` (imágenes WebP, videos MP4/MOV/WebM; máx. 10). El autor sale de la sesión. |
| GET | `/api/social/posts/<id>/` | Detalle (404 si no es visible o está eliminado). |
| PATCH | `/api/social/posts/<id>/` | Edita el texto `{"body"}`. Solo el autor (403 si no). Marca `edited_at`. |
| DELETE | `/api/social/posts/<id>/` | Borrado suave (`deleted_at`). Solo el autor. 204. |
| PUT | `/api/social/posts/<id>/reaction/` | Pone o cambia mi reacción. Body `{"emoji": "<código>"}`. Responde el resumen. |
| DELETE | `/api/social/posts/<id>/reaction/` | Quita mi reacción. Responde el resumen. |
| GET | `/api/social/posts/<id>/reactions/` | Quién reaccionó («Ver todo»), paginado: `user`, `emoji`, `updated_at`. |
| GET | `/api/social/posts/<id>/comments/` | Hilos, más antiguos primero (paginado): comentario raíz con `replies`, `reactions`, `is_mine`, `is_deleted`, `edited_at`. |
| POST | `/api/social/posts/<id>/comments/` | Comenta o responde: `{"body", "parent"?}` (máx. 2000). Responde el comentario y `comments_count`. |
| PATCH | `/api/social/comments/<id>/` | Edita mi comentario `{"body"}` (403 si es ajeno). |
| DELETE | `/api/social/comments/<id>/` | Borrado suave de mi comentario. Responde `comments_count` y `keep_placeholder`. |
| PUT/DELETE | `/api/social/comments/<id>/reaction/` | Pone/cambia o quita mi reacción en un comentario. Responde el resumen. |
| GET | `/api/social/attachments/<id>/file/` | Archivo de un adjunto, solo si su post es visible (`nosniff`, `Cache-Control: private`). |
| GET | `/api/accounts/me/` | Mi perfil. |
| PATCH | `/api/accounts/me/` | Cambia mi presentación `{"bio"}` (máx. 280). Cargo, área y fecha de nacimiento solo desde el admin. |
| POST/DELETE | `/api/accounts/me/avatar/` | Sube (multipart `file`, WebP) o quita mi foto. Se guarda como `avatars/<id>.webp`. |
| GET | `/api/accounts/users/?search=&page=` | Directorio de personas activas, por nombre, **25 por página**: `count`, `page`, `total_pages`, `next`, `previous`, `results` (`id`, `name`, `initials`, `avatar_url`, `email`, `job_title`, `department`, `is_me`, `is_following`). Página inexistente → 404 con `detail`, `page`, `count`, `total_pages`. |
| GET | `/api/accounts/users/<id>/` | Perfil de un empleado activo: `name`, `initials`, `email`, `job_title`, `department`, `bio`, `avatar_url`, `date_joined`, `birthday` (`{day, month}` o `null`, nunca el año), `is_me`, `posts_count`, `follow`. |
| GET | `/api/accounts/users/<id>/avatar/` | Foto (solo con sesión, `nosniff`); la URL lleva `?v=` para la caché. |
| GET | `/api/social/posts/?author=<id>` · `?id=<id>` | Publicaciones de una persona (perfil) · una sola publicación (página `/posts/<id>/`). |
| PUT/DELETE | `/api/social/follows/<id>/` | Seguir / dejar de seguir (inmediato). Responde `followers_count`, `following_count`, `is_following`, `follows_me`. |
| GET | `/api/social/users/<id>/followers/` · `/following/` | Listas paginadas: `id`, `name`, `initials`, `avatar_url`, `job_title`, `is_following`, `is_me`. |
| GET | `/api/social/photos/?author=<id>` | Fotos de sus publicaciones visibles (perfil → «Fotos»), paginado: `id`, `url`, `width`, `height`, `post`. |
| GET | `/api/notifications/?page=` | Mis avisos (25 por página): `id`, `title`, `body`, `icon`, `color`, `url`, `created_at`, `is_read`. |
| GET | `/api/accounts/birthdays/` | Cumpleaños de hoy y los próximos 30 días (máx. 6): `id`, `name`, `initials`, `avatar_url`, `job_title`, `day`, `month`, `days_until`, `is_today`. Nunca el año. |
| GET | `/api/social/follows/suggestions/` | Hasta 5 personas que aún no sigo (misma área primero), mismo formato que las listas de seguidores. |
| POST | `/accounts/google/login/` | Inicia «Continuar con Google» (solo POST con CSRF; GET regresa al login). Retorno: `/accounts/google/login/callback/`. |
| GET | `/api/catalogs/emojis/` | Catálogo de emojis (sin paginar, público): `code`, `char`, `label`, `svg_url`, `lottie_url`, `is_active`. |

  Cada post incluye `comments_count` y `reactions`: `{"reactions": [{"emoji", "count"}], "total", "mine"}` (más usadas primero). El feed usa 3 consultas sin importar cuántas reacciones haya.

  Todas requieren sesión (`SessionAuthentication` + CSRF en escrituras). Respuesta de un post: `id`, `body`, `created_at`, `updated_at`, `author {id, name, initials, avatar_url}`.
- **Inicio de sesión:** `/accounts/login/` (usuario o correo + contraseña, y Google) y `/accounts/logout/` (POST). Ver sección 7.
- **Frontend:** la portada es un *shell*; `static/assets/js/feed.js` pide `/api/social/posts/` (5 por página, scroll infinito), clona `<template id="ws-post-template">` (`components/posts/post_card.html`) y crea publicaciones con `POST`.
- **Sigue en demostración:** solo la lista de accesos rápidos de Inicio (`selectors/demo.py`); todos llevan a páginas reales. Buscar ya no usa datos de prueba.
- **Reacciones con emojis (implementado y probado):** 134 emojis Noto en `catalogs.Emoji`, una reacción por persona y post (`social.PostReaction`). Detalle en `docs/reaction-emojis.md`.

- **Fechas:** Day.js 1.11.13 local en `static/assets/vendor/dayjs/` (relativeTime, localizedFormat, locale `es`); helper `Workspace.time` en `workspace.js`.
- **Backlog por tandas:** `docs/backlog.md`.
- **Media en publicaciones (implementado y probado):** solo imágenes y videos (sin documentos). Detalle en `docs/media-uploads.md`.
- **Borrado suave:** `Post.deleted_at` y `PostComment.deleted_at`. Los selectores nunca devuelven lo eliminado (404 en detalle, reacciones, comentarios y archivos). El borrado definitivo queda pendiente de política (ver backlog).
- **Perfil (implementado y probado; teléfono y escritorio con pestañas Todo · Información · Seguidores · Fotos):** página `/profile/?user_id=<id>` en `apps.accounts.views.profile` (shell) + `static/assets/js/profile.js`. Reutiliza el feed (`components/posts/feed.html`, `feed_modals.html`, `feed_scripts.html`) filtrado por autor. Portada estática. Las fotos de perfil nunca salen de `/media/`: se entregan por la vista autorizada.
- **Seguir y audiencias (implementado y probado):** `social.Follow` (sin solicitud). `Post.audience`: `company` (toda la empresa) o `followers` (autor + seguidores). La regla vive en `selectors.posts.visible_posts` y se aplica a feed, detalle, comentarios, reacciones, fotos y archivos (lo que no puedes ver responde 404). El perfil (`/api/accounts/users/<id>/`) incluye `follow`.
- **Scroll:** `html { scrollbar-gutter: stable }` y se anula la compensación de Bootstrap (`body { padding-right: 0 !important }`, `.sticky-top { margin-right: 0 !important }`) para que nada se mueva al abrir modales.
- **Paginación preparada (`apps/core/pagination.py`):** `SafePageNumberPagination` (25 por página) responde 404 con `count` y `total_pages` cuando la página no existe (`?page=999`, `0`, `abc`); la página 1 siempre es válida. `api_exception_handler` (registrado en `REST_FRAMEWORK["EXCEPTION_HANDLER"]`) agrega esos datos como números. Es la paginación de **toda** la API (`DEFAULT_PAGINATION_CLASS`); `?page_size=` permite pedir menos (máx. 25).
- **Directorio (implementado y probado):** página `/people/` (`apps.accounts.views.people`) + `static/assets/js/people.js`. Botón Seguir compartido en `static/assets/js/follow.js` (perfil, listas y directorio).
- **Organigrama (implementado):** página `/people/org/` (`apps.org.views.org_chart`), pestaña junto al Directorio (`components/people/tabs.html`) + `static/assets/js/org_chart.js` con d3-org-chart (`vendor/d3-org-chart/`). Datos de `/api/org/chart/?depth=10` (árbol por `User.manager`).
- **Avisos = notificaciones (solo tabla y vista):** app `apps.notifications`, modelo simple (título, descripción, ícono, color, fecha y enlace; no depende de ninguna app). Página `/notifications/` titulada «Avisos», destino de la campana y de la pestaña «Avisos» (ya no es una vista de la portada). Todavía no se generan, no se marcan como leídos y no hay contador (ver backlog). `/posts/<id>/?comments=1&comment=<id>` queda como destino para avisos de publicaciones.

- **Pantallas grandes:** `layouts/app.html` es una cuadrícula (`.ws-shell`): ≥ 992px menú fijo (`offcanvas-lg`) + contenido; ≥ 1200px en Inicio, columna de widgets (cumpleaños, personas que quizás conozcas, avisos recientes). Detalle en `docs/backlog.md` («Pantallas grandes»).
- **Secciones (páginas propias):** Buscar `/search/` (filtros; «Personas» busca en el directorio, lo demás «Próximamente»), Calendario `/calendar/` (FullCalendar: Mes, Semana, Agenda; aún sin fechas del sistema), Noticias `/blog/`, Documentos `/documents/`, Formularios `/forms/`, Marketplace `/marketplace/`, Mesa de ayuda `/helpdesk/`, Ayuda `/help/`, Términos `/terms/` y Privacidad `/privacy/` (estas ocho, en construcción con aviso). Vistas en `apps/core/pages.py` y en cada app.
- **Galería de publicaciones:** tocar una foto abre PhotoSwipe a pantalla completa solo con los medios de ese post (incluye los de «+N»); `static/assets/js/lightbox.js`. Teclado, foco de regreso, cerrar arrastrando y «reducir movimiento».
- **App instalable (PWA):** `apps/core/pwa.py` sirve `/manifest.webmanifest` (accesos directos a Avisos, Buscar, Personas y Calendario); íconos en `static/assets/img/icons/`. Pendiente: service worker y botón «Instalar».
- **Correo (preparado):** `apps/core/mail.py` (`send_email`, `absolute_url`), plantillas `templates/emails/`, settings «Correo» en `config/settings/base.py`; producción usa SMTP en cuanto se defina `EMAIL_HOST`.
- **Scripts:** `scripts/` con django-extensions (`runscript`): `scripts.bots.create_bots`, `scripts.bots.create_posts` (personas en `scripts/bots/personas.py`), `fake_media` (ver README).
