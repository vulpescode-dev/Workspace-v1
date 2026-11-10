import { useQuery } from '@tanstack/react-query'

import { ListSkeleton } from '@/components/feedback/ListSkeleton'
import { Widget } from '@/components/ui/Widget'

import { followsApi, followsKeys } from '../api/follows.api'
import { PersonRow } from './PersonRow'

/** «Personas que quizás conozcas» (misma área primero). Si no hay sugerencias, no se muestra. */
export function SuggestionsWidget() {
  const { data, isPending, isError } = useQuery({ queryKey: followsKeys.suggestions(), queryFn: followsApi.suggestions, staleTime: 5 * 60_000 })

  if (isError || (data && data.length === 0)) return null
  return (
    <Widget title="Personas que quizás conozcas">
      {isPending ? (
        <ListSkeleton rows={3} label="Cargando sugerencias" />
      ) : (
        <ul className="grid grid-cols-1 gap-3">
          {data.map((person) => (
            <PersonRow key={person.id} person={person} />
          ))}
        </ul>
      )}
    </Widget>
  )
}
