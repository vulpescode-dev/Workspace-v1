# Sistema de diseño

Interfaz moderna, móvil primero, con Tailwind CSS v4. Los tokens viven en `frontend/src/styles/globals.css`
(`@theme`): si cambia un color, una fuente o una curva, se cambia ahí y no en los componentes.

## Dirección visual

- App de trabajo, no red social pública ni panel administrativo genérico.
- Fondo `canvas` (#F5F6FA), tarjetas blancas (`Card`) con borde sutil y sombra mínima, radios amplios (`rounded-2xl`).
- Jerarquía clara: un título por página (`PageHeader`), subtítulo pequeño en gris.
- **Un solo ancho de contenedor** (`max-w-shell`) para el encabezado y todas las páginas: el encabezado nunca cambia de ancho; el contenido se adapta.
- Estados vacío, carga y error diseñados desde el inicio. Nada de datos falsos: lo que no existe dice «Próximamente».

## Color

| Token | Valor | Uso |
|---|---|---|
| `brand-500` | `#0066CC` | Acción principal, enlaces, foco. Escala `brand-50…900`. |
| `accent-400` | `#F4C600` | Destacar con moderación; texto encima `accent-900`. |
| `canvas` / `surface` | `#F5F6FA` / `#FFFFFF` | Fondo de página / tarjetas. |
| `slate-*` | Tailwind | Texto (900 títulos, 600 cuerpo, 500/400 secundario) y bordes (200). |

Modo oscuro: pendiente (fondo previsto `#19181A`).

## Tipografía

**Dos familias, cada una con un papel fijo** (nunca una tercera):

| Familia | Token | Dónde | Pesos |
|---|---|---|---|
| **Inter** (variable, `@fontsource-variable/inter`) | `font-sans` (por defecto) | Todo lo que se lee y se usa: texto, formularios, botones, menús, etiquetas, números. | 400–700 |
| **Montserrat** (local en `public/fonts/`) | `font-display` | Solo títulos: `h1` de página, `h2` de sección y la marca (`Logo`). | 600–800 |

Por qué: Inter está hecha para pantallas a tamaños chicos (UI densa, cifras alineadas); Montserrat da
personalidad de marca en tamaños grandes. `h1` y `h2` ya usan `font-display` por defecto (`globals.css`).
Para un título que no sea `h1/h2`, usar la clase `font-display`. No usar Montserrat en párrafos ni controles.

## Movimiento (guía de Emil Kowalski)

| Regla | Cómo se aplica aquí |
|---|---|
| ¿Debe animarse? Lo que se usa muchas veces al día, no. | Cambiar de página, pestaña o filtro: sin animación. Toasts, menús y la entrada del login: sí. |
| Curvas fuertes, nunca `ease-in` | `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)` (entradas y respuestas), `--ease-in-out` para mover en pantalla, `--ease-drawer` para paneles. |
| Menos de 300 ms | Botones 160 ms, menús 150 ms, entrada de contenido 280 ms. |
| Presionar responde | Utilidad `pressable`: `scale(.97)` en `:active`. Todo botón o enlace-botón la lleva. |
| Nada aparece de la nada | Entradas con `opacity` + `scale(.97)` o `translateY(8px)`; nunca `scale(0)`. |
| Origen correcto | Menús y popovers crecen desde su botón (`origin-top-right` en `UserMenu`). Los modales, desde el centro. |
| Solo `transform` y `opacity` | No animar `height`, `width`, `margin` ni `padding`. Transiciones con propiedades explícitas, nunca `transition-all`. |
| Hover solo con puntero | En Tailwind v4 `hover:` ya aplica solo en dispositivos con puntero (en el teléfono no se queda «pegado»). |
| Accesibilidad | `prefers-reduced-motion` reduce todo a ~1 ms (`globals.css`). |
| Spinners rápidos | `Spinner` gira cada 600 ms: la espera se percibe más corta. |

## Componentes base (`components/ui/`)

`Button` (primary · secondary · outline · ghost; sm · md · lg; `loading`), `Input`, `PasswordInput`
(mostrar/ocultar), `Field` (etiqueta + ayuda/error con `aria-*` conectados), `Card`, `Avatar`, `Alert`,
`Spinner`, `Logo`, `CountBadge`, `Widget`; en `components/feedback/`: `Skeleton`, `ListSkeleton`, `EmptyState`.
Antes de crear uno nuevo, revisar si alguno sirve con una prop más.

## Carga: esqueletos, no spinners

Todo lo que viene de la API muestra un **esqueleto con la misma forma** que el contenido final (tarjeta de
post, círculos de estados, filas de widgets): la página no brinca cuando llegan los datos. El `Spinner`
queda solo para acciones (botón «Publicar») y para «cargando más» al final del feed. Pulso suave
(opacidad), quieto con «reducir movimiento».

## Estados (tipo Instagram)

Solo la **foto de la persona con un aro**, no tarjetas con el contenido: es más ligero (no se descarga
ninguna foto ni video hasta abrir uno) y se entiende de un vistazo.

| Aro | Significado |
|---|---|
| Degradado de marca (amarillo → azul) | Tiene estados sin ver, o es mi estado activo. |
| Gris (`slate-300`) | Ya vi todos sus estados. |
| Sin aro + «+» azul | «Tu estado»: toca para subir una foto o un video (24 horas). |

Entre aro y foto va un borde blanco de 2 px para que el aro se lea sobre cualquier foto.

**Visor de estados** (propio, sin librería: `<img>`/`<video>` nativos con el archivo descargado con sesión):
en teléfono ocupa toda la pantalla; en pantallas más anchas el marco toma la **proporción del estado**
(vertical como teléfono, horizontal a lo ancho, entre 9:16 y 2:1) sin pasar de 92 % del alto ni del ancho.

## Hojas y paneles según la pantalla

- Hojas que suben desde abajo (Vaul) para menús, emojis, comentarios y «Ver todo».
- La **hoja de emojis ocupa todo el ancho** en cualquier pantalla (como el diseño anterior); su contenido
  se alinea con el contenedor de la página. Comentarios y «Ver todo» son hojas centradas con ancho máximo.
- Menús pequeños anclados a un botón (Mi cuenta, «…» de una publicación): componente `Menu`.
- **Columnas laterales** (menú y widgets): fijas bajo el encabezado y con **su propio scroll vertical** si su
  contenido no cabe de alto (barra fina que aparece al pasar el mouse). **Nunca se desbordan a lo ancho**:
  usan `grid-cols-1` (= `minmax(0, 1fr)`) y `overflow-x-hidden`, y los textos largos se cortan con «…».

## Alturas y zonas seguras (teléfono)

- **Siempre `dvh`, nunca `vh`** (ni `h-screen`/`min-h-screen`): en los navegadores de teléfono `100vh` incluye
  la barra de direcciones aunque esté visible y la página queda más alta que la pantalla. `100dvh` se ajusta
  cuando esa barra aparece o desaparece. Ejemplos: `min-h-dvh`, `h-[70dvh]`, `max-h-[calc(100dvh-4rem)]`.
- Lo que va pegado abajo (barra inferior, hojas) respeta `env(safe-area-inset-bottom)` y, si el teléfono no
  tiene zona segura, deja al menos 0.5 rem: `pb-[max(env(safe-area-inset-bottom),0.5rem)]`.
- El contenido deja abajo el alto de la barra + la zona segura para que nada quede tapado.

## Accesibilidad mínima

Etiquetas reales en formularios, foco visible (`:focus-visible` en `brand-500`), áreas táctiles ≥ 40 px,
`aria-expanded`/`aria-haspopup` en menús, «Saltar al contenido», textos de 16 px en inputs del teléfono
(iOS no hace zoom), zoom del navegador permitido y zonas seguras (`env(safe-area-inset-*)`).
