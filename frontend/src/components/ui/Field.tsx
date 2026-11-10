import { useId, type ReactNode } from 'react'

/**
 * Etiqueta + control + ayuda/error, con los `id` y `aria-*` ya conectados.
 * Uso: `<Field label="Correo">{(props) => <Input {...props} />}</Field>`
 */
export interface FieldControlProps {
  id: string
  'aria-describedby'?: string
  invalid?: boolean
}

interface FieldProps {
  label: string
  hint?: string
  error?: string
  children: (props: FieldControlProps) => ReactNode
}

export function Field({ label, hint, error, children }: FieldProps) {
  const id = useId()
  const messageId = `${id}-message`
  const message = error || hint
  // `content-start`: junto a otro campo más alto (p. ej. uno con ayuda abajo), la cuadrícula no reparte el
  // espacio sobrante entre etiqueta y control; así los controles de una misma fila quedan alineados.
  return (
    <div className="grid content-start gap-1.5">
      <label htmlFor={id} className="text-sm font-semibold text-slate-700">
        {label}
      </label>
      {children({ id, invalid: Boolean(error), 'aria-describedby': message ? messageId : undefined })}
      {message && (
        <p id={messageId} className={error ? 'text-sm text-red-600' : 'text-sm text-slate-500'}>
          {message}
        </p>
      )}
    </div>
  )
}
