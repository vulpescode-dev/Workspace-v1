import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import type { ReactNode } from 'react'
import { Drawer } from 'vaul'

import { useMediaQuery } from '@/hooks/useMediaQuery'
import { cn } from '@/lib/cn'

const sizes = { md: 'md:max-w-lg', lg: 'md:max-w-2xl' } as const

interface SheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: ReactNode
  /** Algo junto al título (p. ej. «Quitar mi reacción»). */
  headerAction?: ReactNode
  /** Ancho del modal en escritorio. */
  size?: keyof typeof sizes
  /** Altura fija (listas que crecen: comentarios, reacciones); sin esto, se ajusta al contenido. */
  tall?: boolean
  /** Se abre desde otra hoja (Vaul la apila en lugar de cerrar la de abajo). */
  nested?: boolean
  /** Hoja del teléfono a todo el ancho (sin tope de 32 rem). */
  fullWidthOnPhone?: boolean
  /** Vaul: mover la hoja al abrir el teclado. Desactivar si la caja de texto está fija abajo. */
  repositionInputs?: boolean
  children: ReactNode
}

/**
 * Hoja que sube desde abajo en el teléfono (se cierra arrastrando, como iOS) y **modal centrado** desde
 * 768 px, donde una hoja inferior queda cortada y con mucho espacio vacío. El contenido es el mismo: el
 * componente solo pone el marco, el título y, en escritorio, el botón de cerrar. Los hijos manejan su
 * propio scroll (`overflow-y-auto`) dentro de un contenedor flex en columna.
 */
export function Sheet({ open, onOpenChange, title, headerAction, size = 'md', tall = false, nested = false, fullWidthOnPhone = false, repositionInputs, children }: SheetProps) {
  const desktop = useMediaQuery('(min-width: 768px)')

  if (desktop) {
    return (
      <Dialog.Root open={open} onOpenChange={onOpenChange}>
        <Dialog.Portal>
          <Dialog.Overlay className="ws-overlay fixed inset-0 z-50 bg-slate-950/40" />
          <Dialog.Content aria-describedby={undefined}
            className={cn('ws-dialog fixed top-1/2 left-1/2 z-50 flex max-h-[85dvh] w-[calc(100%-2rem)] -translate-x-1/2 -translate-y-1/2 flex-col rounded-2xl bg-surface pb-4 shadow-2xl shadow-slate-950/20 outline-none', sizes[size], tall && 'h-[80dvh]')}>
            <div className="flex items-center gap-3 px-5 pt-4 pb-3">
              <Dialog.Title className="min-w-0 flex-1 truncate font-display text-lg font-bold text-slate-900">{title}</Dialog.Title>
              {headerAction}
              <Dialog.Close aria-label="Cerrar" className="pressable -mr-1.5 grid size-9 shrink-0 place-items-center rounded-full text-slate-500 transition-colors duration-150 hover:bg-slate-100 hover:text-slate-800">
                <X className="size-5" aria-hidden />
              </Dialog.Close>
            </div>
            {children}
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    )
  }

  const Root = nested ? Drawer.NestedRoot : Drawer.Root
  return (
    <Root open={open} onOpenChange={onOpenChange} repositionInputs={repositionInputs}>
      <Drawer.Portal>
        <Drawer.Overlay className="fixed inset-0 z-50 bg-slate-950/40" />
        <Drawer.Content aria-describedby={undefined}
          className={cn('fixed inset-x-0 bottom-0 z-50 mx-auto flex flex-col rounded-t-3xl bg-surface pb-[max(env(safe-area-inset-bottom),1rem)] outline-none',
            tall ? 'h-[88dvh]' : 'max-h-[92dvh]', !fullWidthOnPhone && 'max-w-lg')}>
          <div aria-hidden className="mx-auto mt-3 mb-1 h-1.5 w-10 shrink-0 rounded-full bg-slate-300" />
          <div className="flex items-center gap-3 px-5 pt-2 pb-3">
            <Drawer.Title className="min-w-0 flex-1 truncate font-display text-lg font-bold text-slate-900">{title}</Drawer.Title>
            {headerAction}
          </div>
          {children}
        </Drawer.Content>
      </Drawer.Portal>
    </Root>
  )
}
