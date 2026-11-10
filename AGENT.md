# AGENT.md — Instrucciones para agentes

Lee esto y revisa el código real antes de modificarlo. Si la documentación difiere del código, señala la
discrepancia y corrige uno u otro de forma explícita.

## Antes de empezar

1. [`docs/contexto.md`](docs/contexto.md) — qué es el producto, alcance y lo que está **fuera** (p. ej. cursos tipo Udemy).
2. [`docs/checklist.md`](docs/checklist.md) — qué está hecho, qué falta y qué está por decidir. «¿Qué falta?» se responde desde ahí.
3. La arquitectura del lado que vas a tocar: [`docs/arquitectura/backend.md`](docs/arquitectura/backend.md) o [`docs/arquitectura/frontend.md`](docs/arquitectura/frontend.md).
4. Para interfaz: [`docs/frontend/diseno.md`](docs/frontend/diseno.md) (Tailwind, Inter + Montserrat, movimiento de Emil Kowalski).

## Reglas

- **Responder en español.**
- **Por tandas:** al cerrar una tanda, actualizar `docs/checklist.md` (hecho / pendiente / por decidir).
- **Backend solo API.** Nada de plantillas HTML ni vistas de páginas en Django (excepto correos en `templates/emails/`).
- **Configuración en `.env`.** Nunca hosts, nombres, llaves ni URLs fijos en el código; agregar la variable a `.env.example` con comentario.
- **Endpoints:** única raíz `/api/` sin versión; documentar cada uno en `docs/backend/api.md`.
- **Frontend por features:** reutilizar componentes (`components/ui`, `features/<x>/components`); páginas delgadas; datos solo con TanStack Query vía `features/<x>/api` y hooks.
- **Seguridad en el servidor:** permisos y visibilidad se validan en el backend; ocultar un botón no es seguridad.
- **Todo pasa por permisos:** cada acción nueva necesita su permiso en `apps/accounts/data/permissions.json`,
  `require_permission(...)` en el servicio, `useCan()` en React y su prueba (ver `docs/backend/permisos.md`).
  Lo básico que todos deben poder hacer se da con un rol por defecto (`is_default`), no saltándose el permiso.
- **Pruebas por tipo** en `backend/tests/<tipo>/`; en el frontend, `*.test.ts` junto al código (Vitest). No afirmar
  que algo se probó si no se ejecutó.
- **Sin Docker** en esta etapa. Sin Redis, Celery ni WebSockets.
- No inventar datos de catálogos (emojis, categorías…): los define el responsable del proyecto.
- Migraciones: una `0001_initial` por app (consolidadas en noviembre de 2026). No borrar ni consolidar migraciones aplicadas ni ejecutar acciones
  destructivas sin autorización y sin explicar consecuencias.
- Commits y PRs sin atribución a herramientas de IA.
