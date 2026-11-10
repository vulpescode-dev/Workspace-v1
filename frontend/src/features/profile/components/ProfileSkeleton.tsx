import { Skeleton, SkeletonGroup } from '@/components/feedback/Skeleton'
import { Card } from '@/components/ui/Card'

/** Misma forma que el encabezado del perfil + pestañas: nada brinca al llegar los datos. */
export function ProfileSkeleton() {
  return (
    <SkeletonGroup label="Cargando perfil" className="grid gap-4">
      <Card className="overflow-hidden">
        <Skeleton className="h-32 rounded-none sm:h-48" />
        <div className="flex flex-col items-center gap-4 px-4 pb-6 sm:px-8 lg:flex-row lg:items-end">
          <Skeleton className="-mt-14 size-30 rounded-full border-4 border-surface sm:-mt-20 sm:size-38" />
          <div className="grid w-full max-w-sm justify-items-center gap-2 lg:justify-items-start lg:pb-2">
            <Skeleton className="h-7 w-56" />
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-4 w-64" />
          </div>
        </div>
      </Card>
      <div className="flex gap-2">
        {Array.from({ length: 4 }, (_, index) => <Skeleton key={index} className="h-9 w-24 rounded-full" />)}
      </div>
    </SkeletonGroup>
  )
}
