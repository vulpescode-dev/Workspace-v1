import { NavLink } from 'react-router'

import { legalNav } from '@/app/navigation'
import { env } from '@/config/env'
import { cn } from '@/lib/cn'

const YEAR = new Date().getFullYear()

/** Pie de los menús: Términos · Privacidad · ©. */
export function LegalFooter({ onNavigate, className }: { onNavigate?: () => void; className?: string }) {
  return (
    <footer className={cn('flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-400', className)}>
      {legalNav.map((item) => (
        <NavLink key={item.to} to={item.to} onClick={onNavigate} className="hover:text-slate-600">
          {item.label}
        </NavLink>
      ))}
      <span>
        © {YEAR} {env.projectName}
      </span>
    </footer>
  )
}
