"""Avisos que genera la red social (reacciones, comentarios, respuestas y seguidores).

Un solo lugar decide quién recibe qué; los servicios de social solo llaman a estas funciones.
Reglas:
- Nadie recibe avisos de sus propias acciones.
- Cada aviso lleva una clave del evento (``social.<tipo>:<post>:…``): cambiar de emoji actualiza el mismo
  aviso (no se duplica ni vuelve a sonar) y deshacer la acción lo retira.
- Si se elimina una publicación o un comentario, se retiran los avisos que dependen de él.
"""
from apps.notifications.models import Notification
from apps.notifications.services.notifications import notify, withdraw

EXCERPT_LENGTH = 70


def _excerpt(text: str, fallback: str) -> str:
    text = " ".join((text or "").split())
    if not text:
        return fallback
    return f"«{text[:EXCERPT_LENGTH]}…»" if len(text) > EXCERPT_LENGTH else f"«{text}»"


def _name(user) -> str:
    return user.get_full_name() or user.username


# --- Reacciones -------------------------------------------------------------------

def post_reacted(*, post, user, emoji) -> None:
    if post.author_id == user.pk:
        return
    notify(
        recipient=post.author, key=f"social.post_reaction:{post.pk}:{user.pk}",
        title=f"{_name(user)} reaccionó a tu publicación",
        body=f"{emoji.char} {_excerpt(post.body, 'tu publicación')}",
        icon="bx-heart", color=Notification.Color.DANGER, url=f"/posts/{post.pk}/",
    )


def post_reaction_removed(*, post, user) -> None:
    withdraw(key=f"social.post_reaction:{post.pk}:{user.pk}")


def comment_reacted(*, comment, user, emoji) -> None:
    if comment.author_id == user.pk:
        return
    notify(
        recipient=comment.author, key=f"social.comment_reaction:{comment.post_id}:{comment.pk}:{user.pk}",
        title=f"{_name(user)} reaccionó a tu comentario",
        body=f"{emoji.char} {_excerpt(comment.body, 'tu comentario')}",
        icon="bx-heart", color=Notification.Color.DANGER, url=f"/posts/{comment.post_id}/?comments=1",
    )


def comment_reaction_removed(*, comment, user) -> None:
    withdraw(key=f"social.comment_reaction:{comment.post_id}:{comment.pk}:{user.pk}")


# --- Comentarios y respuestas --------------------------------------------------------

def _comment_key(comment, recipient_id: int) -> str:
    return f"social.comment:{comment.post_id}:{comment.pk}:{recipient_id}"


def comment_created(*, comment) -> None:
    """Avisa al autor de la publicación y, si es una respuesta, a quien escribió el comentario respondido.
    Si ambos son la misma persona recibe un solo aviso (el de respuesta, que es más específico)."""
    author = comment.author
    post = comment.post
    url = f"/posts/{post.pk}/?comments=1"
    body = _excerpt(comment.body, "")
    notified = {author.pk}

    parent = comment.parent
    if parent is not None and parent.deleted_at is None and parent.author_id not in notified:
        notify(
            recipient=parent.author, key=_comment_key(comment, parent.author_id),
            title=f"{_name(author)} respondió a tu comentario", body=body,
            icon="bx-comment", color=Notification.Color.PRIMARY, url=url,
        )
        notified.add(parent.author_id)

    if post.author_id not in notified:
        notify(
            recipient=post.author, key=_comment_key(comment, post.author_id),
            title=f"{_name(author)} comentó tu publicación", body=body,
            icon="bx-comment", color=Notification.Color.PRIMARY, url=url,
        )


def comment_edited(*, comment) -> None:
    """El aviso muestra el texto nuevo (sin volver a avisar)."""
    Notification.objects.filter(key__startswith=f"social.comment:{comment.post_id}:{comment.pk}:").update(
        body=_excerpt(comment.body, "")[: Notification._meta.get_field("body").max_length]
    )


def comment_deleted(*, comment) -> None:
    withdraw(prefix=f"social.comment:{comment.post_id}:{comment.pk}:")
    withdraw(prefix=f"social.comment_reaction:{comment.post_id}:{comment.pk}:")


# --- Publicaciones y seguidores -------------------------------------------------------

def post_deleted(*, post) -> None:
    """Al eliminar una publicación se retiran todos los avisos que llevan a ella."""
    for kind in ("post_reaction", "comment", "comment_reaction"):
        withdraw(prefix=f"social.{kind}:{post.pk}:")


def followed(*, follower, target) -> None:
    notify(
        recipient=target, key=f"social.follow:{follower.pk}:{target.pk}",
        title=f"{_name(follower)} empezó a seguirte", body=follower.job_title or "",
        icon="bx-user-plus", color=Notification.Color.SUCCESS, url=f"/profile/{follower.pk}",
    )


def unfollowed(*, follower, target) -> None:
    withdraw(key=f"social.follow:{follower.pk}:{target.pk}")
