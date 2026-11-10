import { useQuery } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { ArrowLeft, FileX } from 'lucide-react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router'

import { EmptyState } from '@/components/feedback/EmptyState'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { postsApi } from '@/features/posts/api/posts.api'
import { postsKeys } from '@/features/posts/api/query-keys'
import { PostCard } from '@/features/posts/components/PostCard'
import { PostCardSkeleton } from '@/features/posts/components/PostCardSkeleton'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'

/**
 * /posts/:id — una publicación sola, con el texto completo (a donde llevan los avisos).
 * `?comments=1` abre los comentarios directamente.
 */
export function PostDetailPage() {
  const { postId } = useParams()
  const id = Number(postId)
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const post = useQuery({ queryKey: postsKeys.detail(id), queryFn: () => postsApi.get(id), enabled: Number.isInteger(id) })
  useDocumentTitle(post.data ? `Publicación de ${post.data.author.name}` : 'Publicación')

  return (
    <div className="mx-auto grid w-full max-w-xl gap-4">
      <Link to="/" className="inline-flex w-fit items-center gap-2 rounded-lg text-sm font-semibold text-slate-500 hover:text-slate-800">
        <ArrowLeft className="size-4" aria-hidden /> Inicio
      </Link>
      {post.isPending ? (
        <PostCardSkeleton withMedia />
      ) : post.isError ? (
        <Card>
          {isAxiosError(post.error) && post.error.response?.status === 404 ? (
            <EmptyState icon={FileX} title="Esta publicación ya no está disponible" description="Puede que se haya eliminado o que no tengas acceso a ella." />
          ) : (
            <EmptyState icon={FileX} title="No se pudo cargar la publicación" action={<Button variant="outline" onClick={() => void post.refetch()}>Reintentar</Button>} />
          )}
        </Card>
      ) : (
        <PostCard post={post.data} expanded openComments={params.get('comments') === '1'} onDeleted={() => navigate('/', { replace: true })} />
      )}
    </div>
  )
}
