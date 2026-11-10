import { Skeleton, SkeletonGroup } from './Skeleton'

/** Esqueleto de una lista de personas/avisos: círculo + dos líneas por fila. */
export function ListSkeleton({ rows = 3, label = 'Cargando' }: { rows?: number; label?: string }) {
  return (
    <SkeletonGroup label={label} className="grid grid-cols-1 gap-3">
      {Array.from({ length: rows }, (_, index) => (
        <div key={index} className="flex items-center gap-3">
          <Skeleton className="size-10 shrink-0 rounded-full" />
          <div className="grid flex-1 gap-1.5">
            <Skeleton className="h-3.5 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
      ))}
    </SkeletonGroup>
  )
}
