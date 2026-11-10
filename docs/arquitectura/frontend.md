# Arquitectura del frontend

React 19 + TypeScript + Vite, con Tailwind CSS v4. Organización **por features** (dominios del producto)
sobre una base de componentes compartidos, para que el proyecto crezca por tandas sin terminar con todo
en una sola carpeta.

## Stack

| Pieza | Para qué |
|---|---|
| **Vite** | Servidor de desarrollo (reenvía `/api`, `/media`, `/static` al backend) y build. |
| **TypeScript** | Tipos de la API y de los componentes: los errores aparecen al escribir, no en producción. |
| **React Router 7** | Rutas, guards (con/sin sesión) y layouts anidados. |
| **TanStack Query** | Datos del servidor: caché, carga, errores, reintentos e invalidación. |
| **axios** | Cliente HTTP con interceptores (Bearer + refresh automático). |
| **Tailwind CSS v4** | Estilos con utilidades y tokens de diseño en `styles/globals.css` (`@theme`). |
| **sonner** | Toasts (de Emil Kowalski). |
| **vaul** | Hojas que suben desde abajo (de Emil Kowalski): menú «Más», emojis, comentarios, «Ver todo». |
| **lottie-web** (SVG) | Emojis animados; se carga solo cuando algo se anima. |
| **d3-org-chart** 3.1.1 | Organigrama (sobre D3 y d3-flextree); se carga solo en la pestaña Organigrama. |
| **lucide-react** | Íconos (una sola familia). |
| **clsx + tailwind-merge** | `cn()` para combinar clases sin conflictos. |

## Estructura

```text
frontend/
├── index.html · vite.config.ts · tsconfig*.json · package.json
├── .env / .env.example         # VITE_PROJECT_NAME, VITE_PROJECT_CODE, VITE_API_URL, BACKEND_URL…
├── public/                     # se sirve tal cual: fonts/ (Montserrat), icons/ (favicon, PWA)
└── src/
    ├── main.tsx                # punto de entrada: fuentes, estilos, proveedores y router
    ├── app/                    # ensamblado de la app
    │   ├── AppProviders.tsx    # QueryClient → AuthProvider → Toaster
    │   ├── navigation.ts       # mapa de navegación: barra inferior, hoja «Más», menú lateral, «Próximamente»
    │   └── router.tsx          # TODAS las rutas: guard → layout → página
    ├── config/env.ts           # única lectura de import.meta.env
    ├── styles/globals.css      # Tailwind + tokens (@theme): colores, fuentes, curvas, ancho del contenedor
    ├── lib/                    # utilidades sin React y sin dominio
    │   ├── api/                # client.ts (axios + JWT), token-store.ts, errors.ts
    │   ├── query-client.ts
    │   ├── format.ts           # fechas en español, tiempo relativo («hace 5 min»)
    │   ├── media/to-webp.ts    # reducir y convertir fotos a WebP antes de subir
    │   └── cn.ts
    ├── hooks/                  # hooks genéricos (useDocumentTitle, useProtectedImage, useInView…)
    ├── types/                  # tipos compartidos de la API (Paginated<T>…)
    ├── components/             # piezas SIN conocimiento del negocio
    │   ├── ui/                 # Button, Input, PasswordInput, Field, Card, Avatar, Alert, Spinner, Logo, CountBadge, Widget, Menu, Tabs
    │   ├── layout/             # AppLayout, AppHeader, AuthLayout, PageHeader
    │   │   └── navigation/     # BottomNav (teléfono), MoreSheet (hoja «Más» con Vaul), SideNav (escritorio), LegalFooter
    │   ├── feedback/           # EmptyState, FullPageLoader, Skeleton, ListSkeleton
    │   └── media/              # ProtectedImage (foto con sesión + esqueleto)
    ├── features/               # un dominio del producto por carpeta
    │   ├── auth/               # api/, context/ (AuthProvider, useAuth), hooks/ (useLogout), guards/, components/ (LoginForm, GoogleButton), utils/
    │   ├── accounts/           # api/, hooks/ (useMe), components/ (UserAvatar, UserMenu), types.ts
    │   ├── notifications/      # useUnreadCount, useNotifications/acciones, NotificationBell, NotificationList, NotificationItem, utils/appearance (íconos y colores)
    │   ├── posts/              # PostCard (única), PostFeed (scroll infinito), PostComposer, PostEditor, PostGallery, PostCardSkeleton, AudienceToggle
    │   ├── reactions/          # useEmojis, AnimatedEmoji (Lottie bajo demanda), ReactionSheet (hoja animada), ReactionSummaryChips, ReactionListSheet
    │   ├── comments/           # CommentsSheet (hilos + escribir), CommentItem, useComments
    │   ├── stories/            # StoryTray (fila con aros), StoryRing, StoryViewer (pantalla completa), StoryViewersPanel («Visto por»)
    │   ├── follows/            # FollowButton, PersonRow (reutilizables), SuggestionsWidget
    │   ├── profile/            # ProfileHeader, ProfileInfo, ProfilePhotos, ProfilePeople, EditProfileSheet, ProfileSkeleton
    │   └── people/             # PeopleDirectory, PersonCard, OrgChartView (d3-org-chart, carga diferida)
    └── pages/                  # una por ruta; DELGADAS: solo componen features
        ├── LoginPage · HomePage · NotificationsPage · PostDetailPage · ProfilePage · PeoplePage · ComingSoonPage · NotFoundPage
```

### Anatomía de una feature

```text
features/<dominio>/
├── api/
│   ├── <dominio>.api.ts    # funciones que llaman a la API con `api` (lib/api/client)
│   └── query-keys.ts       # llaves de caché de TanStack Query
├── hooks/                  # useAlgo(): envuelven useQuery/useMutation; los componentes usan estos
├── components/             # componentes del dominio (PostCard, ReactionPicker…)
├── utils/                  # lógica pura del dominio
└── types.ts                # tipos de lo que responde la API
```

Solo se crean las carpetas que se usan.

## Reglas

1. **¿Dónde va un componente?**
   - No sabe nada del negocio (botón, tarjeta, modal) → `components/ui/`.
   - Es del negocio (tarjeta de post, menú de cuenta) → `features/<dominio>/components/`.
   - Es una ruta → `pages/` y solo compone piezas de features.
2. **Reutilizar, no copiar.** Un mismo concepto = un solo componente. Ejemplo: `PostCard` vivirá en
   `features/posts/components/` y lo usarán Inicio, Perfil, Detalle del post y Búsqueda. Las variaciones
   se piden con props explícitas (`compact`, `showAuthor`), nunca copiando el archivo.
3. **Componentes visuales puros.** Los de `components/ui/` reciben datos por props y no llaman a la API
   (p. ej. `Avatar` recibe `src`; `UserAvatar` en `features/accounts` es quien descarga la foto).
4. **Datos del servidor solo con TanStack Query** a través de hooks de la feature (`useMe`). Nada de
   `useEffect` + `fetch` sueltos en componentes.
5. **Nunca llamar a axios directamente**: siempre `features/<x>/api/` → `lib/api/client`.
6. **Importaciones con `@/`** (`@/components/ui/Button`). Una feature puede importar de `components/`, `lib/`,
   `hooks/` y de otra feature solo lo que esa feature expone (hooks, componentes, tipos), nunca su `api/` interno.
7. **Variables de entorno** solo desde `config/env.ts`. Las que no llevan `VITE_` nunca llegan al navegador.
8. **Seguridad:** el access token vive en memoria; nada sensible en `localStorage`. Los permisos los decide
   el backend; ocultar un botón es solo comodidad. Para mostrar u ocultar: `useCan()('app.recurso.acción')`
   y, para secciones, `useSectionAccess()` / `RequireAccess` (ver `docs/backend/permisos.md`).
9. **Rutas nuevas** se registran en `app/router.tsx` bajo `RequireAuth` (privadas) o `GuestOnly`, dentro de su
   `RequireAccess section="…"` si la sección tiene permiso. Las páginas se cargan **por ruta**
   (`lazy: page(() => import('@/pages/XPage'), 'XPage')`): cada sección es su propio `.js`. Solo Inicio, Login,
   Avisos y las pantallas de error van en el archivo principal.
10. **Todo lo que viene de la API tiene esqueleto.** Mientras carga se muestra un `Skeleton` con la misma
    forma que el contenido (no un spinner suelto), para que nada brinque. Además: estado de error con
    «Reintentar» y estado vacío honesto. Los cambios del usuario (reaccionar, seguir) son optimistas:
    se ven al instante y se regresan si el servidor falla.
11. **Navegación:** las secciones viven en `app/navigation.ts`. Al terminar una sección: `ready: true` y su
    página en el router (mientras `ready` sea `false`, el router le pone «Próximamente» solo).

## Navegación

| Ancho | Qué se ve |
|---|---|
| < 1024 px | Encabezado (logo, campana, cuenta) + **barra inferior**: Inicio · Avisos · Buscar · Más. «Más» abre una hoja desde abajo con las aplicaciones (cuadrícula de 3), la cuenta, cerrar sesión y el pie legal. |
| ≥ 1024 px | Encabezado + **menú lateral** fijo (15 rem, alineado con el logo): Principal · Aplicaciones · Cuenta (con Cerrar sesión) · pie legal. Sin barra inferior. Las rutas con `handle: { fullWidth: true }` (perfil) van sin menú lateral. |

- Máximo 4 destinos en la barra (caben con etiqueta desde 320 px). Perfil y favoritos no son destinos principales.
- «Más» se marca activo cuando la página actual es de la hoja.
- Cambiar de pestaña no se anima; la hoja sí (Vaul: curva tipo iOS, cerrar arrastrando con un movimiento rápido).

## Errores

- **404, 500 y sin conexión** a pantalla completa, con emojis animados (`components/feedback/ErrorScene.tsx`).
  La raíz del router atrapa cualquier error al dibujar (`RouteErrorPage`), también si no se puede descargar
  una página (sin red → «Sin conexión»; versión nueva publicada → «Algo salió mal» con «Recargar»).
- `OfflineGate` vigila la red: sin conexión muestra la pantalla sin desmontar la página (lo escrito no se pierde)
  y al volver avisa «¡De vuelta en línea!». Sus emojis se precargan para verse sin red.
- Vista previa en desarrollo: `/dev/errors/404`, `/dev/errors/500`, `/dev/errors/offline`.
- Errores de la API: avisos (`sonner`) con el mensaje del servidor (`getErrorMessage`) y estados de
  «No se pudo cargar» con «Reintentar» en las listas.

## Sesión en el frontend

- `AuthProvider` intenta recuperar la sesión al abrir la app (`POST /api/auth/refresh/` con la cookie) y
  expone `status` (`loading` / `authenticated` / `unauthenticated`), `login()` y `logout()`.
- `RequireAuth` manda a `/login?next=<ruta>`; `GuestOnly` saca del login a quien ya entró. `safeNext()`
  solo acepta rutas internas (evita redirecciones a otros sitios).
- Detalle del flujo de tokens: `docs/backend/autenticacion.md`.

## Comandos

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (el backend debe estar en :8000)
npm run build      # tsc + vite build → dist/
npm run lint       # oxlint (solo src/)
npm test           # Vitest: pruebas de lógica pura (*.test.ts junto al código)
```
