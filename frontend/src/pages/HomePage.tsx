import type { Section } from '@/features/accounts/access'
import { BirthdaysWidget } from '@/features/accounts/components/BirthdaysWidget'
import { SuggestionsWidget } from '@/features/follows/components/SuggestionsWidget'
import { useCan, useSectionAccess } from '@/features/accounts/hooks/useCan'
import { PostComposer } from '@/features/posts/components/PostComposer'
import { PostFeed } from '@/features/posts/components/PostFeed'
import { StoryTray } from '@/features/stories/components/StoryTray'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'

/**
 * / — Inicio: estados, «¿Qué quieres compartir?» y el feed. En pantallas anchas (≥ 1280 px) se suma
 * la columna de widgets a la derecha (cumpleaños y personas sugeridas).
 */
export function HomePage() {
  useDocumentTitle('Inicio')
  const can = useCan()
  const { ready, canSee } = useSectionAccess()
  // Aquí no se adivina: hasta saber mis permisos no se pide nada de otras secciones (evita 403).
  const show = (section: Section) => ready && canSee(section)
  return (
    <div className="xl:grid xl:grid-cols-[minmax(0,1fr)_18rem] xl:gap-8">
      <div className="mx-auto grid w-full max-w-xl gap-4">
        <h1 className="sr-only">Inicio</h1>
        {show('stories') && <StoryTray />}
        {can('social.posts.create') && <PostComposer />}
        {show('posts') && <PostFeed />}
      </div>
      {/* Fija junto al feed y con su propio scroll VERTICAL: si los widgets no caben de alto, se desplazan.
          grid-cols-1 (= minmax(0, 1fr)) impide que un nombre largo ensanche la columna: se corta con «…». */}
      <aside aria-label="Widgets" className="hidden min-w-0 xl:block">
        <div className="sticky top-16 -mt-8 grid max-h-[calc(100dvh-4rem)] grid-cols-1 content-start gap-4 overflow-x-hidden overflow-y-auto overscroll-contain py-8 pr-1 [scrollbar-color:transparent_transparent] [scrollbar-width:thin] hover:[scrollbar-color:var(--color-slate-300)_transparent]">
          {show('people') && <BirthdaysWidget />}
          <SuggestionsWidget />
        </div>
      </aside>
    </div>
  )
}
