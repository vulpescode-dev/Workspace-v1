import type { Emoji } from '@/features/reactions/types'
import { preloadLottie } from '@/features/reactions/utils/lottie'

import bandageLottie from '@/assets/emoji/bandage_face.json?url'
import bandageSvg from '@/assets/emoji/bandage_face.svg'
import dizzyLottie from '@/assets/emoji/dizzy_face.json?url'
import dizzySvg from '@/assets/emoji/dizzy_face.svg'
import fireLottie from '@/assets/emoji/fire.json?url'
import fireSvg from '@/assets/emoji/fire.svg'
import questionLottie from '@/assets/emoji/question.json?url'
import questionSvg from '@/assets/emoji/question.svg'
import monkeyLottie from '@/assets/emoji/see_no_evil_monkey.json?url'
import monkeySvg from '@/assets/emoji/see_no_evil_monkey.svg'
import sleepLottie from '@/assets/emoji/sleep.json?url'
import sleepSvg from '@/assets/emoji/sleep.svg'
import slothLottie from '@/assets/emoji/sloth.json?url'
import slothSvg from '@/assets/emoji/sloth.svg'
import thinkingLottie from '@/assets/emoji/thinking_face.json?url'
import thinkingSvg from '@/assets/emoji/thinking_face.svg'

/**
 * Emojis de las pantallas de error. Viven en el frontend (no en el catálogo del backend) porque deben
 * verse aunque la API esté caída o no haya red.
 */
const emoji = (code: string, char: string, label: string, svg_url: string, lottie_url: string): Emoji =>
  ({ code, char, label, svg_url, lottie_url, is_active: true })

export const ERROR_EMOJIS = {
  thinking: emoji('thinking_face', '🤔', 'Cara pensativa', thinkingSvg, thinkingLottie),
  question: emoji('question', '❓', 'Signo de interrogación', questionSvg, questionLottie),
  monkey: emoji('see_no_evil_monkey', '🙈', 'Mono que no ve', monkeySvg, monkeyLottie),
  dizzy: emoji('dizzy_face', '😵', 'Cara mareada', dizzySvg, dizzyLottie),
  fire: emoji('fire', '🔥', 'Fuego', fireSvg, fireLottie),
  bandage: emoji('bandage_face', '🤕', 'Cara con vendaje', bandageSvg, bandageLottie),
  sloth: emoji('sloth', '🦥', 'Perezoso', slothSvg, slothLottie),
  sleep: emoji('sleep', '😴', 'Cara dormida', sleepSvg, sleepLottie),
}

/** Deja listos (en memoria y caché del navegador) los emojis de «Sin conexión» mientras todavía hay red. */
export function preloadOfflineEmojis() {
  const { sloth, sleep } = ERROR_EMOJIS
  for (const item of [sloth, sleep]) new Image().src = item.svg_url
  preloadLottie([sloth.lottie_url, sleep.lottie_url])
}
