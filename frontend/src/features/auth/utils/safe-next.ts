/** Solo rutas internas en `?next=` (evita mandar a otro sitio tras el login: open redirect). */
export function safeNext(next: string | null): string {
  if (!next || !next.startsWith('/') || next.startsWith('//') || next.startsWith('/\\')) return '/'
  return next
}
