import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { toast } from 'sonner'

import { ReactionListSheet } from '@/features/reactions/components/ReactionListSheet'
import { ReactionPicker } from '@/features/reactions/components/ReactionPicker'
import { ReactionSummaryChips } from '@/features/reactions/components/ReactionSummaryChips'
import { getErrorMessage } from '@/lib/api/errors'

import { blogApi, blogKeys, type ArticleDetail } from '../api/blog.api'

/** Reacciones del artículo: pastillas (tocar la mía la quita), «Reaccionar» y «Ver todo». Igual que en el muro. */
export function ArticleReactions({ article }: { article: ArticleDetail }) {
  const queryClient = useQueryClient()
  const { mine } = article.reactions
  const [celebrate, setCelebrate] = useState<{ code: string; key: number } | null>(null)
  const [showAll, setShowAll] = useState(false)
  const [everShown, setEverShown] = useState(false)

  const react = useMutation({
    mutationFn: (emoji: string | null) => (emoji ? blogApi.react(article.id, emoji) : blogApi.unreact(article.id)),
    onSuccess: (reactions) => {
      queryClient.setQueryData<ArticleDetail>(blogKeys.detail(article.id), (current) => current && { ...current, reactions })
      void queryClient.invalidateQueries({ queryKey: blogKeys.reactions(article.id) })
    },
    onError: (error) => toast.error(getErrorMessage(error, 'No se pudo guardar tu reacción.')),
  })

  function choose(code: string | null) {
    react.mutate(code)
    if (code) setCelebrate({ code, key: Date.now() })
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <ReactionPicker mine={mine} onPick={choose} disabled={react.isPending} />
      <ReactionSummaryChips
        summary={article.reactions}
        onToggle={(code) => choose(code === mine ? null : code)}
        celebrate={celebrate}
        onShowAll={() => { setEverShown(true); setShowAll(true) }}
      />
      {everShown && (
        <ReactionListSheet
          open={showAll}
          onOpenChange={setShowAll}
          summary={article.reactions}
          queryKey={blogKeys.reactions(article.id)}
          fetchPage={(page) => blogApi.reactions(article.id, page)}
        />
      )}
    </div>
  )
}
