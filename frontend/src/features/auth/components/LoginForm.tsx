import { useState, type FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router'

import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { Input } from '@/components/ui/Input'
import { PasswordInput } from '@/components/ui/PasswordInput'
import { getErrorMessage } from '@/lib/api/errors'

import { useAuth } from '../context/useAuth'
import { safeNext } from '../utils/safe-next'

/** Usuario **o** correo + contraseña. Un solo mensaje genérico para cualquier fallo (no revela qué cuentas existen). */
export function LoginForm() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const username = String(form.get('username') ?? '').trim()
    const password = String(form.get('password') ?? '')
    if (!username || !password) {
      setError('Escribe tu usuario o correo y tu contraseña.')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      await login({ username, password })
      navigate(safeNext(params.get('next')), { replace: true })
    } catch (err) {
      setError(getErrorMessage(err))
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="grid gap-4">
      {error && <Alert tone="error">{error}</Alert>}
      <Field label="Usuario o correo">
        {(props) => <Input {...props} name="username" autoComplete="username" autoCapitalize="none" spellCheck={false} placeholder="nombre@empresa.com" autoFocus />}
      </Field>
      <Field label="Contraseña">
        {(props) => <PasswordInput {...props} name="password" autoComplete="current-password" />}
      </Field>
      <Button type="submit" size="lg" loading={submitting} className="mt-2 w-full">
        Iniciar sesión
      </Button>
    </form>
  )
}
