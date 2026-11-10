import type { AnimationItem } from 'lottie-web'

/**
 * Emojis animados (Noto Animated Emoji, Lottie). Peso controlado:
 * - el reproductor (lottie-web SVG con expresiones, ~250 KB; la versión «light» dejaba en blanco emojis como «Heart hands») se descarga la primera vez que algo se anima;
 * - cada animación (8–235 KB) se descarga solo cuando ese emoji se anima, y queda en memoria.
 * Con «reducir movimiento» no se anima nada.
 */
type LottiePlayer = typeof import('lottie-web').default

let playerPromise: Promise<LottiePlayer> | null = null
const animations = new Map<string, Promise<unknown>>()

function loadPlayer() {
  playerPromise ??= import('lottie-web/build/player/lottie_svg').then((module) => module.default as unknown as LottiePlayer)
  return playerPromise
}

function loadAnimation(url: string) {
  if (!animations.has(url)) {
    animations.set(url, fetch(url).then((response) => {
      if (!response.ok) throw new Error(`No se pudo cargar ${url}`)
      return response.json()
    }))
  }
  return animations.get(url)!
}

/** Descarga el reproductor y estas animaciones sin mostrarlas (p. ej. las de «Sin conexión», que deben estar listas antes de perder la red). */
export function preloadLottie(urls: string[]) {
  if (prefersReducedMotion()) return
  void loadPlayer().catch(() => undefined)
  for (const url of urls) void loadAnimation(url).catch(() => animations.delete(url))
}

export const prefersReducedMotion =() => window.matchMedia('(prefers-reduced-motion: reduce)').matches

/**
 * Monta y reproduce una animación en `container`. Devuelve la instancia (o `null` si no se debe animar).
 * `signal`: si se cancela mientras se descarga, no se crea nada. Importa: destruir una animación vacía
 * todo su contenedor, así que una creada tarde borraría a la que ya se estaba viendo.
 */
export async function playLottie(container: HTMLElement, url: string, loop: boolean, signal?: AbortSignal): Promise<AnimationItem | null> {
  if (prefersReducedMotion()) return null
  const [player, animationData] = await Promise.all([loadPlayer(), loadAnimation(url)])
  if (!container.isConnected || signal?.aborted) return null
  return player.loadAnimation({ container, renderer: 'svg', loop, autoplay: true, animationData })
}
