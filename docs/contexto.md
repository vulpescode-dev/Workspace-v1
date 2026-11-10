# Contexto del proyecto

## Qué es Workspace

Intranet empresarial y mesa de trabajo digital para ~500 personas (con capacidad de crecer), de la empresa
con dominio **@orienta.soy** y sede en Querétaro. No es una red social pública, ni solo una intranet, ni un
clon de Google Workspace: es una plataforma integrada con tres dimensiones.

1. **Capa social y colaboración:** publicaciones internas, comentarios, reacciones, adjuntos, seguir personas.
2. **Capa de intranet:** avisos oficiales, documentos corporativos, información por áreas, organigrama,
   accesos según roles y permisos.
3. **Apps de productividad:** formularios (estilo Google Forms), mesa de ayuda, marketplace interno,
   noticias (blog) y las que se sumen después.

El feed es una puerta de entrada importante, pero **no define todo el producto**. Documentos, avisos,
formularios y las demás apps son módulos de primera clase.

### Regla para decidir

Toda pantalla, modelo o función nueva debe decir a qué dimensión pertenece y cómo se integra con las demás.
Si mejora el feed pero dificulta encontrar documentos o formularios, no es automáticamente una mejora.

## Estado actual (noviembre 2026)

El proyecto se **reestructuró** en dos partes:

- **`backend/`** — Django + DRF, solo API y admin. Conserva todos los modelos, servicios y APIs de la
  versión anterior (social, avisos, documentos, mesa de ayuda, blog, marketplace, organigrama…), con JWT activo.
- **`frontend/`** — React desde cero con Tailwind. Por ahora solo **Login** e **Inicio** (bienvenida).
  Las pantallas que existían en la versión con plantillas de Django (Bootstrap + jQuery) se reconstruyen
  en React **por tandas**, reutilizando las APIs que ya existen.

Avance detallado en [`checklist.md`](checklist.md).

## Alcance

### Dentro

Feed social, avisos/notificaciones (y push), documentos con versiones y privacidad, formularios,
mesa de ayuda, noticias (blog), marketplace, directorio de personas, perfil, organigrama, departamentos,
calendario, búsqueda, cumpleaños, roles y permisos, permisos/vacaciones (por definir con RH), correo
saliente (no-reply@), PWA instalable.

### Fuera de alcance (decidido)

- **Cursos tipo Udemy / plataforma de capacitación (LMS).** No se hará.
- **Nómina, sueldos y expediente de RH.** El alcance de RH se limita a estructura (departamentos, jefes) y permisos.
- **Microservicios.** El backend es un monolito modular.
- **Docker** (en esta etapa), Redis, Celery y WebSockets (en esta etapa).
- **Registro abierto con contraseña.** Las cuentas sin Google las crea TI.

## Personas usuarias

| Rol | Qué necesita |
|---|---|
| Persona empleada | Enterarse de avisos y novedades, encontrar documentos y formularios, contactar personas, pedir ayuda. Mayormente desde el **teléfono**. |
| Jefe / responsable de área | Lo anterior + su equipo en el organigrama, aprobar solicitudes (futuro). |
| Agente de mesa de ayuda | Atender tickets de su departamento. |
| RRHH / Comunicación | Publicar avisos y noticias, administrar documentos y formularios. |
| TI / Administración | Cuentas, roles, permisos y catálogos desde `/admin/`. |

## Cómo se trabaja

- **Por tandas** (fases/sprints): cada tanda cierra actualizando `checklist.md` (hecho / pendiente / por decidir).
  Cuando se pregunte «¿qué falta?», la respuesta sale de ahí.
- Documentación junto con el código: si cambia una decisión, se cambia el doc en el mismo paso.
- No se inventan datos ni resultados de pruebas; lo que no existe dice «Próximamente».
- Marca visible: **Workspace** (sale de `PROJECT_NAME` / `VITE_PROJECT_NAME`). Colores: azul `#0066CC`, amarillo `#F4C600`.
