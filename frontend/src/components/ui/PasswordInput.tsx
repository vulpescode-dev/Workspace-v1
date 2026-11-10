import { Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'

import { Input, type InputProps } from './Input'

/** Contraseña con botón para mostrarla (útil en teléfono, donde es fácil equivocarse al escribir). */
export function PasswordInput(props: Omit<InputProps, 'type'>) {
  const [visible, setVisible] = useState(false)
  const Icon = visible ? EyeOff : Eye
  return (
    <div className="relative">
      <Input {...props} type={visible ? 'text' : 'password'} className="pr-12" />
      <button
        type="button"
        onClick={() => setVisible((value) => !value)}
        aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
        aria-pressed={visible}
        className="pressable absolute inset-y-0 right-1 my-auto grid size-10 place-items-center rounded-lg text-slate-400 hover:text-slate-600"
      >
        <Icon className="size-5" aria-hidden />
      </button>
    </div>
  )
}
