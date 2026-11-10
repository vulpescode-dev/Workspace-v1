/** «2026-11-07» en hora local (nunca `toISOString`, que pasa a UTC y puede cambiar el día). */
export function dayKey(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
export function parseDay(key: string) {
  const [year, month, day] = key.split('-').map(Number)
  return new Date(year, month - 1, day)
}
export const addDays = (date: Date, days: number) => new Date(date.getFullYear(), date.getMonth(), date.getDate() + days)

/** Semanas (de lunes a domingo) que cubren el mes: 5 o 6 filas de 7 días. */
export function monthWeeks(year: number, month: number): Date[][] {
  const first = new Date(year, month, 1)
  const start = addDays(first, -((first.getDay() + 6) % 7))
  const last = new Date(year, month + 1, 0)
  const end = addDays(last, 6 - ((last.getDay() + 6) % 7))
  const weeks: Date[][] = []
  for (let day = start; day <= end; day = addDays(day, 7)) weeks.push(Array.from({ length: 7 }, (_, i) => addDays(day, i)))
  return weeks
}

const capitalize = (text: string) => text.charAt(0).toUpperCase() + text.slice(1)
const dayFormat = new Intl.DateTimeFormat('es-MX', { weekday: 'long', day: 'numeric', month: 'long' })
export const formatDayTitle = (date: Date) => capitalize(dayFormat.format(date))
const monthFormat = new Intl.DateTimeFormat('es-MX', { month: 'long', year: 'numeric' })
export const formatMonth = (date: Date) => capitalize(monthFormat.format(date))
