import { Users } from 'lucide-react'

import { EmptyState } from '@/components/feedback/EmptyState'
import { ListSkeleton } from '@/components/feedback/ListSkeleton'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { PersonRow } from '@/features/follows/components/PersonRow'

import { profileApi, profileKeys } from '../api/profile.api'
import { usePagedList } from '../hooks/useProfile'

/** Pestaña Seguidores: Seguidores y Seguidos lado a lado en escritorio, uno debajo del otro en teléfono. */
export function ProfilePeople({ userId }: { userId: number }) {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <PeopleColumn userId={userId} kind="followers" title="Seguidores" empty="Todavía no tiene seguidores." />
      <PeopleColumn userId={userId} kind="following" title="Seguidos" empty="Todavía no sigue a nadie." />
    </div>
  )
}

function PeopleColumn({ userId, kind, title, empty }: { userId: number; kind: 'followers' | 'following'; title: string; empty: string }) {
  const list = usePagedList(profileKeys.people(userId, kind), (page) => profileApi[kind](userId, page))
  const people = list.data?.pages.flatMap((page) => page.results) ?? []
  const total = list.data?.pages[0]?.count

  return (
    <Card className="min-w-0 p-5">
      <h2 className="mb-4 text-base font-bold text-slate-900">
        {title}
        {total !== undefined && <span className="ml-2 font-medium text-slate-400 tabular-nums">{total}</span>}
      </h2>
      {list.isPending ? (
        <ListSkeleton rows={4} label={`Cargando ${title.toLowerCase()}`} />
      ) : list.isError ? (
        <p className="text-sm text-slate-500">No se pudo cargar la lista.</p>
      ) : people.length === 0 ? (
        <EmptyState icon={Users} title={empty} />
      ) : (
        <ul className="grid grid-cols-1 gap-3">
          {people.map((person) => (
            <PersonRow key={person.id} person={person} />
          ))}
        </ul>
      )}
      {list.hasNextPage && (
        <Button variant="ghost" size="sm" className="mt-3 w-full" loading={list.isFetchingNextPage} onClick={() => void list.fetchNextPage()}>
          Ver más
        </Button>
      )}
    </Card>
  )
}
