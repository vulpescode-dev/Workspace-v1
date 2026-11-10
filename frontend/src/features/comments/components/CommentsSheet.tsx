import { Sheet } from '@/components/ui/Sheet'

import { postCommentSource } from '../api/comments.api'
import { CommentsPanel } from './CommentsPanel'

interface CommentsSheetProps {
  postId: number
  open: boolean
  onOpenChange: (open: boolean) => void
  onCountChange: (count: number) => void
}

/**
 * Comentarios de una publicación: hoja que sube desde abajo en el teléfono y modal en escritorio (como el
 * diseño anterior). Hilos con respuestas de un nivel; la caja para escribir queda fija abajo.
 */
export function CommentsSheet({ postId, open, onOpenChange, onCountChange }: CommentsSheetProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange} repositionInputs={false} title="Comentarios" tall>
      <CommentsPanel source={postCommentSource(postId)} enabled={open} onCountChange={onCountChange} inSheet />
    </Sheet>
  )
}
