/**
 * El servidor solo acepta imágenes WebP (ver docs/backend/media-uploads.md): el navegador las reduce y
 * convierte antes de subir. Así viajan y se guardan hasta 10 veces más ligeras que la foto original.
 */
export interface WebpOptions {
  /** Lado mayor máximo en píxeles (se conserva la proporción). */
  maxSide?: number
  /** 0–1. 0.82 se ve igual y pesa mucho menos. */
  quality?: number
}

export async function toWebp(file: File, { maxSide = 2048, quality = 0.82 }: WebpOptions = {}): Promise<File> {
  const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' }).catch(() => {
    throw new Error(`«${file.name}» no es una imagen que se pueda abrir.`)
  })
  const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height))
  const width = Math.round(bitmap.width * scale)
  const height = Math.round(bitmap.height * scale)

  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  canvas.getContext('2d')!.drawImage(bitmap, 0, 0, width, height)
  bitmap.close()

  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/webp', quality))
  // Algunos navegadores viejos devuelven PNG en lugar de WebP: mejor avisar que subir algo que el servidor rechaza.
  if (!blob || blob.type !== 'image/webp') throw new Error('Tu navegador no puede preparar la imagen. Actualízalo e inténtalo de nuevo.')
  const name = file.name.replace(/\.[^.]+$/, '') || 'imagen'
  return new File([blob], `${name}.webp`, { type: 'image/webp' })
}

export const isVideo = (file: File) => file.type.startsWith('video/')
export const isImage = (file: File) => file.type.startsWith('image/')
