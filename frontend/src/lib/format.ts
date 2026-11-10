/**
 * Formatos de fecha y número en español. La API manda ISO 8601 con desfase y aquí se muestra en la
 * zona horaria de quien ve la página (Intl, sin librerías).
 */
const longDate = new Intl.DateTimeFormat('es-MX', { weekday: 'long', day: 'numeric', month: 'long' })
const shortDate = new Intl.DateTimeFormat('es-MX', { day: 'numeric', month: 'short' })
const shortDateYear = new Intl.DateTimeFormat('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })
const fullDateTime = new Intl.DateTimeFormat('es-MX', { dateStyle: 'full', timeStyle: 'short' })
const relative = new Intl.RelativeTimeFormat('es-MX', { numeric: 'auto' })

const toDate = (value: Date | string) => (typeof value === 'string' ? new Date(value) : value)

/** «sábado, 7 de noviembre» con mayúscula inicial. */
export function formatLongDate(value: Date | string) {
  const text = longDate.format(toDate(value))
  return text.charAt(0).toUpperCase() + text.slice(1)
}

/** Fecha y hora completas (para el `title` de un `<time>`). */
export function formatFullDateTime(value: Date | string) {
  return fullDateTime.format(toDate(value))
}

/**
 * Tiempo relativo corto como en las redes: «ahora», «hace 5 min», «hace 3 h», «ayer», «hace 4 días»;
 * desde una semana, la fecha («2 nov», o «2 nov 2025» si es de otro año).
 */
export function formatRelative(value: Date | string, now = new Date()) {
  const date = toDate(value)
  const seconds = Math.round((now.getTime() - date.getTime()) / 1000)
  if (seconds < 45) return 'ahora'
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `hace ${minutes} min`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `hace ${hours} h`
  const days = Math.round(hours / 24)
  if (days < 7) return relative.format(-days, 'day')
  return (date.getFullYear() === now.getFullYear() ? shortDate : shortDateYear).format(date)
}
