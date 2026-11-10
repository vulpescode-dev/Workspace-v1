import type { InputHTMLAttributes } from 'react'

import { cn } from '@/lib/cn'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean
}

/** Campo de texto base. Texto de 16px en teléfono para que iOS no haga zoom al enfocarlo. */
export function Input({ invalid, className, ...props }: InputProps) {
  return (
    <input
      aria-invalid={invalid || undefined}
      className={cn(
        'h-12 w-full rounded-xl border border-slate-200 bg-surface px-4 text-base text-slate-900 sm:text-sm',
        'placeholder:text-slate-400 transition-[border-color,box-shadow] duration-150 ease-out',
        'focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none',
        'aria-invalid:border-red-400 aria-invalid:focus:ring-red-500/15',
        'disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500',
        className,
      )}
      {...props}
    />
  )
}
