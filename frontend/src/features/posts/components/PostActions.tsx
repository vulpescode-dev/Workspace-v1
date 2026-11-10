import { MessageCircle } from 'lucide-react'
import { useState } from 'react'

import { ReactionListSheet } from '@/features/reactions/components/ReactionListSheet'
import { ReactionPicker } from '@/features/reactions/components/ReactionPicker'
import { ReactionSummaryChips } from '@/features/reactions/components/ReactionSummaryChips'

import { postsApi } from '../api/posts.api'
import { postsKeys } from '../api/query-keys'
import { useReactToPost } from '../hooks/usePostMutations'
import type { Post } from '../types'

/** Resumen de reacciones («Ver todo») + «Reaccionar» y comentarios. */
export function PostActions({ post, onComment }: { post: Post; onComment: () => void }) {
  const react = useReactToPost()
  const { mine } = post.reactions
  const [celebrate, setCelebrate] = useState<{ code: string; key: number } | null>(null)
  const [showAll, setShowAll] = useState(false)
  const [everShown, setEverShown] = useState(false)

  function choose(code: string | null) {
    react.mutate({ post, emoji: code })
    if (code) setCelebrate({ code, key: Date.now() })   // se anima una vez en su pastilla
  }

  // Tocar mi misma pastilla la quita; cualquier otra la pone o la cambia.
  const toggle = (code: string) => choose(code === mine ? null : code)

  return (
    <div className="px-4 pt-3 pb-3">
      <ReactionSummaryChips summary={post.reactions} onToggle={toggle} celebrate={celebrate} onShowAll={() => {
        setEverShown(true)
        setShowAll(true)
      }} />
      <div className="mt-2 flex items-center gap-1 border-t border-slate-100 pt-2">
        <ReactionPicker mine={mine} onPick={choose} />
        <button
          type="button"
          onClick={onComment}
          className="pressable flex h-9 items-center gap-2 rounded-xl px-3 text-sm font-semibold text-slate-600 transition-colors duration-150 hover:bg-slate-100"
        >
          <MessageCircle className="size-5" aria-hidden />
          {post.comments_count > 0 ? `${post.comments_count} ${post.comments_count === 1 ? 'comentario' : 'comentarios'}` : 'Comentar'}
        </button>
      </div>
      {everShown && (
        <ReactionListSheet
          open={showAll}
          onOpenChange={setShowAll}
          summary={post.reactions}
          queryKey={postsKeys.reactions(post.id)}
          fetchPage={(page) => postsApi.reactions(post.id, page)}
        />
      )}
    </div>
  )
}
