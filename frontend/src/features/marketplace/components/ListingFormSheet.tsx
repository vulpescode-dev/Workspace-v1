import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ImagePlus, X } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'
import { Sheet } from '@/components/ui/Sheet'

import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { Input } from '@/components/ui/Input'
import { getErrorMessage } from '@/lib/api/errors'
import { toWebp } from '@/lib/media/to-webp'

import { MAX_LISTING_IMAGES, marketplaceApi, marketplaceKeys, type Listing, type ListingCategory } from '../api/marketplace.api'
import { ListingPhoto } from './ListingPhoto'

const selectClass = 'h-12 w-full rounded-xl border border-slate-200 bg-surface px-3 text-base text-slate-900 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm'

interface NewPhoto { key: string; file: File; preview: string }

/**
 * Publicar o editar un anuncio: fotos (hasta 10; se convierten a WebP en el navegador), título, precio
 * (vacío = «A tratar»), categoría y descripción. Al editar, las fotos que quites o agregues se aplican al guardar.
 */
export function ListingFormSheet({ listing, categories, onClose }: { listing?: Listing; categories: ListingCategory[]; onClose: () => void }) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const fileInput = useRef<HTMLInputElement>(null)
  const [title, setTitle] = useState(listing?.title ?? '')
  const [price, setPrice] = useState(listing?.price ? String(Number(listing.price)) : '')
  const [category, setCategory] = useState(listing?.category?.id ?? 0)
  const [description, setDescription] = useState(listing?.description ?? '')
  const [kept, setKept] = useState(listing?.images ?? [])
  const [added, setAdded] = useState<NewPhoto[]>([])
  const [preparing, setPreparing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Libera las vistas previas al cerrar la hoja.
  const addedRef = useRef(added)
  useEffect(() => { addedRef.current = added }, [added])
  useEffect(() => () => addedRef.current.forEach((photo) => URL.revokeObjectURL(photo.preview)), [])

  const total = kept.length + added.length
  const options = listing?.category && !categories.some((item) => item.id === listing.category!.id) ? [listing.category, ...categories] : categories

  async function pick(files: FileList | null) {
    const picked = Array.from(files ?? []).filter((file) => file.type.startsWith('image/'))
    if (!picked.length) return
    const room = MAX_LISTING_IMAGES - total
    if (picked.length > room) toast.error(`Máximo ${MAX_LISTING_IMAGES} fotos por anuncio.`)
    setPreparing(true)
    try {
      const ready = await Promise.all(picked.slice(0, room).map((file) => toWebp(file, { maxSide: 1600 })))
      setAdded((current) => [...current, ...ready.map((file) => ({ key: crypto.randomUUID(), file, preview: URL.createObjectURL(file) }))])
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo preparar la foto.')
    } finally {
      setPreparing(false)
    }
  }

  function dropAdded(photo: NewPhoto) {
    URL.revokeObjectURL(photo.preview)
    setAdded((current) => current.filter((item) => item.key !== photo.key))
  }

  const save = useMutation({
    mutationFn: async (): Promise<Listing> => {
      const values = { title: title.trim(), description: description.trim(), price: price.trim() || null, category: category || null }
      if (!listing) {
        const form = new FormData()
        form.append('title', values.title)
        form.append('description', values.description)
        form.append('price', values.price ?? '')
        form.append('category', category ? String(category) : '')
        added.forEach((photo) => form.append('files', photo.file))
        return marketplaceApi.create(form)
      }
      const changes: Parameters<typeof marketplaceApi.update>[1] = {}
      if (values.title !== listing.title) changes.title = values.title
      if (values.description !== listing.description) changes.description = values.description
      if ((values.price === null ? null : Number(values.price)) !== (listing.price === null ? null : Number(listing.price))) changes.price = values.price
      if (values.category !== (listing.category?.id ?? null)) changes.category = values.category
      let result = Object.keys(changes).length ? await marketplaceApi.update(listing.id, changes) : listing
      const removed = listing.images.filter((image) => !kept.some((item) => item.id === image.id))
      for (const image of removed) await marketplaceApi.removeImage(image.id)
      if (added.length) result = await marketplaceApi.addImages(listing.id, added.map((photo) => photo.file))
      else if (removed.length) result = await marketplaceApi.get(listing.id)
      return result
    },
    onSuccess: (saved) => {
      queryClient.setQueryData(marketplaceKeys.detail(saved.id), saved)
      void queryClient.invalidateQueries({ queryKey: marketplaceKeys.lists() })
      toast.success(listing ? 'Cambios guardados.' : 'Anuncio publicado.')
      onClose()
      if (!listing) navigate(`/marketplace/${saved.id}`)
    },
    onError: (err) => setError(getErrorMessage(err, 'No se pudo guardar el anuncio.')),
  })

  function submit(event: FormEvent) {
    event.preventDefault()
    if (!title.trim()) return setError('Escribe qué vendes.')
    if (price.trim() && !/^\d+(\.\d{1,2})?$/.test(price.trim())) return setError('Escribe el precio solo con números (por ejemplo 1500 o 249.50), o déjalo vacío para «A tratar».')
    setError(null)
    save.mutate()
  }

  return (
    <Sheet open onOpenChange={(open) => !open && onClose()} repositionInputs={false} title={<>{listing ? 'Editar anuncio' : 'Vender algo'}</>}>
      <form onSubmit={submit} className="grid gap-4 overflow-y-auto px-5 pb-2">
        {error && <Alert tone="error">{error}</Alert>}

        <fieldset className="grid gap-2">
          <legend className="mb-1 flex w-full justify-between text-sm font-semibold text-slate-700">
            Fotos <span className="font-normal text-slate-500 tabular-nums">{total} / {MAX_LISTING_IMAGES}</span>
          </legend>
          <ul className="grid grid-cols-4 gap-2">
            {kept.map((image, index) => (
              <PhotoTile key={image.id} label={`Quitar foto ${index + 1}`} cover={index === 0} onRemove={() => setKept((current) => current.filter((item) => item.id !== image.id))}>
                <ListingPhoto url={image.url} className="size-full" />
              </PhotoTile>
            ))}
            {added.map((photo, index) => (
              <PhotoTile key={photo.key} label={`Quitar foto ${kept.length + index + 1}`} cover={kept.length + index === 0} onRemove={() => dropAdded(photo)}>
                <img src={photo.preview} alt="" className="size-full object-cover" />
              </PhotoTile>
            ))}
            {total < MAX_LISTING_IMAGES && (
              <li>
                <button type="button" onClick={() => fileInput.current?.click()} disabled={preparing}
                  className="pressable grid aspect-square w-full place-items-center rounded-xl border-2 border-dashed border-slate-200 text-slate-500 transition-colors duration-150 hover:border-brand-300 hover:bg-brand-50/40 hover:text-brand-700 disabled:opacity-60">
                  <span className="grid justify-items-center gap-1 text-xs font-semibold"><ImagePlus className="size-5" aria-hidden />{preparing ? 'Preparando…' : 'Agregar'}</span>
                </button>
              </li>
            )}
          </ul>
          <p className="text-xs text-slate-500">La primera foto es la portada del anuncio.</p>
          <input ref={fileInput} type="file" accept="image/*" multiple hidden onChange={(event) => { void pick(event.target.files); event.target.value = '' }} />
        </fieldset>

        <Field label="¿Qué vendes?">{(props) => <Input {...props} value={title} onChange={(event) => setTitle(event.target.value)} maxLength={120} placeholder="Ej.: Silla de oficina ergonómica" />}</Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Precio (MXN)" hint="Vacío = «A tratar»">
            {(props) => <Input {...props} value={price} onChange={(event) => setPrice(event.target.value.replace(/[^\d.]/g, ''))} inputMode="decimal" placeholder="0" />}
          </Field>
          <Field label="Categoría">
            {({ invalid, ...props }) => (
              <select {...props} aria-invalid={invalid || undefined} value={category} onChange={(event) => setCategory(Number(event.target.value))} className={selectClass}>
                <option value={0}>Sin categoría</option>
                {options.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
              </select>
            )}
          </Field>
        </div>
        <Field label="Descripción (opcional)">
          {({ invalid, ...props }) => (
            <textarea {...props} aria-invalid={invalid || undefined} value={description} onChange={(event) => setDescription(event.target.value)} maxLength={3000} rows={4}
              placeholder="Estado, medidas, dónde se entrega…"
              className="w-full resize-none rounded-xl border border-slate-200 bg-surface px-4 py-3 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm" />
          )}
        </Field>

        <div className="flex justify-end gap-2 pt-1">
          <Button variant="ghost" onClick={onClose}>Cancelar</Button>
          <Button type="submit" loading={save.isPending} disabled={preparing}>{listing ? 'Guardar' : 'Publicar'}</Button>
        </div>
      </form>
    </Sheet>
  )
}

function PhotoTile({ label, cover, onRemove, children }: { label: string; cover: boolean; onRemove: () => void; children: ReactNode }) {
  return (
    <li className="relative aspect-square overflow-hidden rounded-xl transition-[opacity,transform] duration-200 ease-out starting:scale-90 starting:opacity-0">
      {children}
      {cover && <span className="absolute bottom-1 left-1 rounded-md bg-slate-900/70 px-1.5 py-0.5 text-[10px] font-bold text-white">Portada</span>}
      <button type="button" aria-label={label} onClick={onRemove} className="pressable absolute top-1 right-1 grid size-6 place-items-center rounded-full bg-slate-900/70 text-white hover:bg-slate-900">
        <X className="size-3.5" aria-hidden />
      </button>
    </li>
  )
}
