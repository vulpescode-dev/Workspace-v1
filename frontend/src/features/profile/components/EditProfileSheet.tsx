import { Camera, Trash2 } from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/Button'
import { Sheet } from '@/components/ui/Sheet'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import type { Profile } from '@/features/accounts/types'
import { getErrorMessage } from '@/lib/api/errors'

import { useEditMyProfile } from '../hooks/useProfile'

const BIO_MAX = 280

/**
 * Editar mi perfil: foto (se reduce a 512 px y pasa a WebP en el navegador) y presentación (280).
 * Nombre, cargo, área y jefe los administra RRHH/TI desde el admin: aquí se explica en lugar de ocultarlo.
 */
export function EditProfileSheet({ profile, open, onOpenChange }: { profile: Profile; open: boolean; onOpenChange: (open: boolean) => void }) {
  const { bio, avatar, removeAvatar } = useEditMyProfile()
  const [draft, setDraft] = useState(profile.bio)
  const inputRef = useRef<HTMLInputElement>(null)
  const fail = (fallback: string) => (error: unknown) =>
    toast.error(error instanceof Error && !('isAxiosError' in error) ? error.message : getErrorMessage(error, fallback))

  function pickPhoto(file: File | undefined) {
    if (!file) return
    avatar.mutate(file, { onSuccess: () => toast.success('Foto actualizada.'), onError: fail('No se pudo cambiar la foto.') })
  }

  function saveBio() {
    bio.mutate(draft.trim(), {
      onSuccess: () => {
        toast.success('Perfil actualizado.')
        onOpenChange(false)
      },
      onError: fail('No se pudo guardar.'),
    })
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange} title="Editar perfil">

      <div className="grid gap-6 overflow-y-auto px-5">
        <section className="flex items-center gap-4">
          <UserAvatar user={profile} size="lg" />
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" loading={avatar.isPending} onClick={() => inputRef.current?.click()}>
              <Camera className="size-4" aria-hidden /> Cambiar foto
            </Button>
            {profile.avatar_url && (
              <Button
                variant="ghost"
                size="sm"
                loading={removeAvatar.isPending}
                onClick={() => removeAvatar.mutate(undefined, { onSuccess: () => toast('Foto quitada.'), onError: fail('No se pudo quitar la foto.') })}
              >
                <Trash2 className="size-4" aria-hidden /> Quitar
              </Button>
            )}
          </div>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            hidden
            onChange={(event) => {
              pickPhoto(event.target.files?.[0])
              event.target.value = ''
            }}
          />
        </section>

        <section className="grid gap-1.5">
          <label htmlFor="profile-bio" className="text-sm font-semibold text-slate-700">
            Presentación
          </label>
          <textarea
            id="profile-bio"
            value={draft}
            onChange={(event) => setDraft(event.target.value.slice(0, BIO_MAX))}
            rows={4}
            placeholder="Cuéntale a tus compañeros a qué te dedicas o qué te gusta."
            className="w-full resize-y rounded-xl border border-slate-200 px-3 py-2.5 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm"
          />
          <p className="text-right text-xs text-slate-400 tabular-nums">
            {draft.length}/{BIO_MAX}
          </p>
        </section>

        <p className="rounded-xl bg-slate-50 px-3 py-2.5 text-xs text-slate-500">
          Tu nombre, cargo, área y jefe directo los actualiza Recursos Humanos o Soporte TI.
        </p>

        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button onClick={saveBio} loading={bio.isPending} disabled={draft.trim() === profile.bio}>
            Guardar
          </Button>
        </div>
      </div>
    </Sheet>
  )
}
