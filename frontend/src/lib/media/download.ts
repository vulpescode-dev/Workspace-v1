import { api } from '@/lib/api/client'

/** Descarga un archivo que pide sesión (con el token) y lo guarda con su nombre original. */
export async function downloadProtected(url: string, filename: string) {
  const { data } = await api.get<Blob>(url, { baseURL: '', responseType: 'blob' })
  const objectUrl = URL.createObjectURL(data)
  const link = Object.assign(document.createElement('a'), { href: objectUrl, download: filename })
  document.body.append(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
}
