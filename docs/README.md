# Documentación de Workspace

| Documento | Qué contiene |
|---|---|
| [contexto.md](contexto.md) | Qué es el producto, estado actual, alcance y lo que queda fuera. |
| [requisitos.md](requisitos.md) | Requisitos funcionales (RF) y no funcionales (RNF). |
| [checklist.md](checklist.md) | Qué módulos están hechos, qué falta, próximas tandas y decisiones pendientes. |
| [arquitectura/backend.md](arquitectura/backend.md) | Django: estructura, convenciones, `.env`, pruebas. |
| [arquitectura/frontend.md](arquitectura/frontend.md) | React: estructura por features, reglas de componentes, sesión. |
| [frontend/diseno.md](frontend/diseno.md) | Colores, tipografía, movimiento (Emil Kowalski), componentes base. |
| [backend/api.md](backend/api.md) | Todos los endpoints de `/api/`. |
| [backend/autenticacion.md](backend/autenticacion.md) | JWT: flujo, cookies, configuración. |
| [backend/permisos.md](backend/permisos.md) | Roles y permisos: catálogo, roles semilla y por defecto, qué exige cada sección y acción, cómo agregar uno. |
| [backend/media-uploads.md](backend/media-uploads.md) | Cómo se suben, validan y entregan fotos y videos. |
| [backend/reaction-emojis.md](backend/reaction-emojis.md) | Catálogo de emojis de reacciones. |

Regla: si cambia una decisión o un endpoint, se actualiza el documento en el mismo paso. Al cerrar una tanda, se actualiza `checklist.md`.
