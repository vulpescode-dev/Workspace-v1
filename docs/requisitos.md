# Requisitos

Identificadores estables (`RF-…`, `RNF-…`) para poder citarlos en tandas y revisiones.
El estado de cada uno está en [`checklist.md`](checklist.md).

## Requisitos funcionales

### Acceso y cuentas
- **RF-ACC-01** Iniciar sesión con usuario **o** correo + contraseña.
- **RF-ACC-02** Mensaje de error genérico que no revele si la cuenta existe o está desactivada.
- **RF-ACC-03** Mantener la sesión al recargar o volver a abrir la app dentro del tiempo del refresh token.
- **RF-ACC-04** Cerrar sesión revocando la sesión en el servidor.
- **RF-ACC-05** «Continuar con Google» solo para cuentas `@orienta.soy` verificadas; primera entrada crea la cuenta.
- **RF-ACC-06** Sin registro abierto: las cuentas sin Google las crea TI.
- **RF-ACC-07** Roles de negocio con permisos `app.recurso.accion[.alcance]`, asignables a varias personas.

### Inicio
- **RF-HOME-01** Bienvenida con el nombre de la persona y la fecha.
- **RF-HOME-02** Feed de publicaciones, avisos importantes y accesos rápidos (por tandas).
- **RF-HOME-03** Widgets: cumpleaños, personas sugeridas, avisos recientes.

### Social
- **RF-SOC-01** Publicar texto con imágenes (WebP) y videos; audiencia «Toda la empresa» o «Solo seguidores».
- **RF-SOC-02** Editar y eliminar (borrado suave) publicaciones y comentarios propios.
- **RF-SOC-03** Comentarios con respuestas de un nivel; reacciones con emojis del catálogo (una por persona).
- **RF-SOC-04** Seguir personas; ver seguidores y seguidos.
- **RF-SOC-05** La tarjeta de publicación es la misma en Inicio, Perfil, Detalle y Búsqueda.
- **RF-SOC-06** Estados tipo Instagram: foto o video que dura 24 horas; en Inicio se muestran como la foto de la persona con un aro de color (sin ver) o gris (visto).

### Avisos (notificaciones)
- **RF-NOT-01** Lista de avisos paginada, marcar leído/no leído/todos, contador, eliminar.
- **RF-NOT-02** Las apps generan avisos con un servicio común (`notify()`).
- **RF-NOT-03** Notificaciones push en dispositivos donde la persona lo acepte.

### Personas y organización
- **RF-ORG-01** Directorio con búsqueda (nombre, correo, cargo, área) y filtros.
- **RF-ORG-02** Perfil: foto, cargo, área, jefe directo, presentación, publicaciones y fotos.
- **RF-ORG-03** Departamentos con subáreas y responsable; organigrama por jefe directo.

### Documentos
- **RF-DOC-01** Subir documentos con categoría y privacidad (empresa, departamentos, personas).
- **RF-DOC-02** Versiones numeradas con nota; restaurar una anterior como versión nueva; descarga autorizada.

### Formularios
- **RF-FRM-01** Crear formularios con preguntas abiertas y cerradas (opción única, casillas, escala, cuadrícula, fecha…).
- **RF-FRM-02** Responder (un envío por persona si se configura) y ver resultados/gráficas.

### Mesa de ayuda
- **RF-HD-01** Levantar tickets por categoría con adjuntos; folio, estados, prioridad.
- **RF-HD-02** Agentes por departamento: atender, asignar, transferir, notas internas, historial.

### Noticias (blog) y Marketplace
- **RF-BLOG-01** Artículos con portada, categorías, borradores y publicación programada; reacciones y comentarios.
- **RF-MKT-01** Anuncios con hasta 10 fotos, precio opcional, estatus disponible/vendido, filtros.

### Otros
- **RF-CAL-01** Calendario con eventos, cumpleaños y avisos con fecha.
- **RF-SRCH-01** Búsqueda general (personas, publicaciones, documentos, avisos, formularios).
- **RF-MAIL-01** Correos salientes desde `no-reply@` con versión HTML y texto.
- **RF-LEAVE-01** Permisos y vacaciones (por definir con RH).

## Requisitos no funcionales

### Arquitectura
- **RNF-ARQ-01** Backend Django + DRF, monolito modular, solo API (`/api/`, sin versión) + admin.
- **RNF-ARQ-02** Frontend React + TypeScript + Tailwind, organizado por features con componentes reutilizables.
- **RNF-ARQ-03** Toda configuración variable en `.env` (backend y frontend); nada de hosts, nombres o llaves en el código.
- **RNF-ARQ-04** Sin Docker, Redis, Celery ni WebSockets en esta etapa.
- **RNF-ARQ-05** SQLite en desarrollo; migración planificada a PostgreSQL.

### Seguridad
- **RNF-SEG-01** JWT: access corto en memoria; refresh en cookie httpOnly, `SameSite=Strict`, rotación y lista negra.
- **RNF-SEG-02** Límite de intentos de login por IP.
- **RNF-SEG-03** Permisos y visibilidad siempre validados en el servidor, también al acceder por ID.
- **RNF-SEG-04** Archivos validados por contenido real (lista permitida); nunca se exponen rutas de `/media/`.
- **RNF-SEG-05** Secretos solo en `.env`, fuera del repositorio. Producción con HTTPS y cookies `Secure`.
- **RNF-SEG-06** Sin redirecciones abiertas (`?next=` solo rutas internas).

### Experiencia de uso
- **RNF-UX-01** Móvil primero; funciona desde 320 px hasta escritorio, con zoom y texto grande.
- **RNF-UX-02** Movimiento según la guía de Emil Kowalski (< 300 ms, ease-out fuerte, `prefers-reduced-motion`).
- **RNF-UX-03** Accesibilidad: etiquetas, foco visible, áreas táctiles ≥ 40 px, contraste suficiente.
- **RNF-UX-04** Estados de carga (esqueletos con la forma del contenido), vacío y error en cada pantalla; nunca datos falsos.
- **RNF-UX-05** Un solo ancho de contenedor para encabezado y páginas.
- **RNF-UX-06** Dos familias tipográficas: Inter (interfaz) y Montserrat (títulos).

### Rendimiento
- **RNF-REN-01** Listas paginadas (25 por página máximo).
- **RNF-REN-02** Caché de datos en el cliente (TanStack Query); sin peticiones duplicadas.
- **RNF-REN-03** Solo se animan `transform` y `opacity`.

### Calidad
- **RNF-CAL-01** Pruebas del backend organizadas por tipo (`auth`, `google`, `api`, `database`, `uploads`, `mail`, `core`).
- **RNF-CAL-02** El frontend compila sin errores de TypeScript ni de lint.
- **RNF-CAL-03** Cada endpoint documentado en `docs/backend/api.md`.
- **RNF-CAL-04** Fechas en ISO 8601 con zona; el navegador las muestra en la zona de quien ve.
