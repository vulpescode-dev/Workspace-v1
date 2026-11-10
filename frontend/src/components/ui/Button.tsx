import type { ButtonHTMLAttributes } from 'react'

import { cn } from '@/lib/cn'

import { Spinner } from './Spinner'

// hover: en Tailwind v4 solo aplica en dispositivos con puntero (no se "pega" al tocar en el teléfono).
const variants = {
  primary: 'bg-brand-500 text-white shadow-sm shadow-brand-900/10 hover:bg-brand-600',
  secondary: 'bg-accent-400 text-accent-900 hover:brightness-95',
  outline: 'border border-slate-200 bg-surface text-slate-700 hover:bg-slate-50',
  soft: 'bg-brand-50 text-brand-700 hover:bg-brand-100',
  ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
} as const

const sizes = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-11 px-4 text-sm',
  lg: 'h-12 px-5 text-base',
} as const

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants
  size?: keyof typeof sizes
  loading?: boolean
}

/** Botón base de la app. `loading` lo deshabilita y muestra un spinner sin cambiar su ancho. */
export function Button({ variant = 'primary', size = 'md', loading = false, disabled, className, children, ...props }: ButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cn(
        'pressable relative inline-flex items-center justify-center gap-2 rounded-xl font-semibold whitespace-nowrap select-none',
        'transition-[background-color,color,filter,transform] duration-150 ease-out',
        'disabled:cursor-not-allowed disabled:opacity-60',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      <span className={cn('inline-flex items-center gap-2 transition-opacity duration-150', loading && 'opacity-0')}>{children}</span>
      {loading && <Spinner className="absolute size-5" />}
    </button>
  )
}
