import { Skeleton } from '@/components/feedback/Skeleton'
import { Card } from '@/components/ui/Card'

/** Misma forma que `PostCard` (cabecera, 3 líneas, foto opcional, acciones): nada brinca al llegar los datos. */
export function PostCardSkeleton({ withMedia = false }: { withMedia?: boolean }) {
  return (
    <Card className="overflow-hidden">
      <div className="flex items-center gap-3 px-4 pt-4">
        <Skeleton className="size-10 rounded-full" />
        <div className="grid flex-1 gap-2">
          <Skeleton className="h-3.5 w-36" />
          <Skeleton className="h-3 w-20" />
        </div>
      </div>
      <div className="grid gap-2 px-4 pt-4">
        <Skeleton className="h-3.5 w-full" />
        <Skeleton className="h-3.5 w-11/12" />
        <Skeleton className="h-3.5 w-2/3" />
      </div>
      {withMedia && <Skeleton className="mt-4 aspect-[4/3] w-full rounded-none" />}
      <div className="mx-4 mt-4 mb-3 flex gap-2 border-t border-slate-100 pt-3">
        <Skeleton className="h-8 w-28 rounded-xl" />
        <Skeleton className="h-8 w-28 rounded-xl" />
      </div>
    </Card>
  )
}
