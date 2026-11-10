import { Globe, Users } from 'lucide-react'

import { AUDIENCE_LABELS, type Audience } from '../types'

/** Para quién es la publicación: alterna «Toda la empresa» / «Solo seguidores». Se usa al crear y al editar. */
export function AudienceToggle({ value, onChange }: { value: Audience; onChange: (value: Audience) => void }) {
  const next: Audience = value === 'company' ? 'followers' : 'company'
  const Icon = value === 'company' ? Globe : Users
  return (
    <button
      type="button"
      onClick={() => onChange(next)}
      title={`Cambiar a: ${AUDIENCE_LABELS[next]}`}
      className="pressable flex h-9 items-center gap-2 rounded-xl px-3 text-sm font-semibold text-slate-600 transition-colors duration-150 hover:bg-slate-100"
    >
      <Icon className="size-4 text-brand-600" aria-hidden />
      {AUDIENCE_LABELS[value]}
    </button>
  )
}
