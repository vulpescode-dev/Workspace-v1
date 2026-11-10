const dayMonth = new Intl.DateTimeFormat('es-MX', { day: 'numeric', month: 'long', timeZone: 'UTC' })
const monthYear = new Intl.DateTimeFormat('es-MX', { month: 'long', year: 'numeric' })

/** «18 de noviembre» (el año —la edad— nunca llega del servidor). */
export function formatBirthday({ day, month }: { day: number; month: number }) {
  return dayMonth.format(Date.UTC(2000, month - 1, day))
}

/** «octubre de 2026». */
export function formatMonthYear(value: string) {
  return monthYear.format(new Date(value))
}
