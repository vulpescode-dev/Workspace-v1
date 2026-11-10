/** Texto plano de una descripción → bloques para mostrarla (párrafos, listas y subtítulos). Lógica pura, probada. */

const BULLET = /^\s*(?:[-•*·]|\d+[.)])\s+/
/** «Incluye:», «Detalles técnicos:»… — una línea corta que termina en dos puntos. */
const isHeading = (line: string) => line.trim().endsWith(':') && line.trim().length <= 48

export type Block = { kind: 'p'; text: string } | { kind: 'ul'; items: string[] } | { kind: 'h'; text: string }

/**
 * Convierte el texto plano tal como lo escribe la gente en bloques legibles, sin pedirles formato:
 * líneas vacías separan párrafos, líneas con «-», «•», «*» o «1.» forman listas y una línea corta que
 * termina en «:» se vuelve subtítulo. Todo lo demás se respeta tal cual (saltos de línea incluidos).
 */
export function toBlocks(text: string): Block[] {
  const blocks: Block[] = []
  let paragraph: string[] = []
  let list: string[] = []
  const flush = () => {
    if (paragraph.length) blocks.push({ kind: 'p', text: paragraph.join('\n') })
    if (list.length) blocks.push({ kind: 'ul', items: list })
    paragraph = []
    list = []
  }
  for (const raw of text.replace(/\r\n/g, '\n').split('\n')) {
    const line = raw.trimEnd()
    if (!line.trim()) flush()
    else if (BULLET.test(line)) {
      if (paragraph.length) flush()
      list.push(line.replace(BULLET, ''))
    } else if (isHeading(line)) {
      flush()
      blocks.push({ kind: 'h', text: line.trim().slice(0, -1) })
    } else {
      if (list.length) flush()
      paragraph.push(line)
    }
  }
  flush()
  return blocks
}
