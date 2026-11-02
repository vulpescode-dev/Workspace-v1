"""Relleno del muro: publicaciones de los bots con su propia voz (solo desarrollo).

    python manage.py runscript scripts.bots.create_posts                     # 24 publicaciones
    python manage.py runscript scripts.bots.create_posts --script-args 40    # otra cantidad

- Cada bot escribe con su personalidad (``personas.py``): sus temas, frases, emojis y largo de
  texto. Las ideas tienen huecos que se llenan al azar, a veces con una frase de apertura o de
  cierre, y no se repite un texto que el mismo bot ya publicó hace poco.
- Unos bots publican más que otros (``activity``) y nunca el mismo dos veces seguidas.
- Tipos: solo texto, texto + 1 a 10 imágenes, solo imágenes, textos largos con saltos de línea y
  publicaciones «Solo seguidores».
- Reacciones, comentarios, respuestas y reacciones a comentarios **solo de quien puede ver la
  publicación** (``visible_posts``, la misma regla que la API) y no en todas: hay publicaciones
  sin ninguna interacción. Quien sigue al autor participa más.
- Todo se crea con los servicios de la app (las mismas validaciones que la API).
- Fechas: repartidas (con huecos irregulares) hasta 10 horas hacia atrás, pero **siempre
  después** de la publicación más reciente que ya exista y en el mismo orden en que se crean. Así
  el orden por fecha coincide con el orden por id (el muro y el admin muestran lo nuevo arriba).
  Comentarios entre su publicación y ahora; cada respuesta, después de su comentario.

Cada corrida agrega publicaciones nuevas sin borrar las anteriores (los bots y sus seguimientos
se reutilizan con ``create_bots``, no se duplican).
"""
import random
import re
from collections import Counter
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.catalogs.models import Emoji
from apps.social.models import Follow, Post, PostComment
from apps.social.selectors.posts import visible_posts
from apps.social.services.comments import create_comment, set_comment_reaction
from apps.social.services.posts import create_post
from apps.social.services.reactions import set_reaction

from scripts.bots.create_bots import get_bots, sync_follows
from scripts.bots.personas import PERSONAS
from scripts.fake_media import photo

DEFAULT_COUNT = 24
SLOT = re.compile(r"\{(\w+)\}")


def _fill(text: str, persona: dict, rng: random.Random, chosen: dict) -> str:
    """Llena los ``{huecos}``; el mismo hueco vale lo mismo en el texto y en el pie de foto."""
    def pick(match):
        key = match.group(1)
        if key not in chosen:
            chosen[key] = rng.choice(persona["fill"][key])
        return chosen[key]
    return SLOT.sub(pick, text)


def _compose(persona: dict, idea: tuple, rng: random.Random) -> tuple[str, int, str | None, str]:
    """Texto final, número de fotos, audiencia y pie de foto de una idea."""
    text, photos, audience, caption = idea
    chosen = {}
    body = _fill(text, persona, rng, chosen)
    caption = _fill(caption, persona, rng, chosen)
    if isinstance(photos, tuple):
        photos = rng.randint(*photos)

    if body:
        sep = "\n\n" if "\n" in body or len(body) > 90 else " "
        if persona["openers"] and rng.random() < 0.25:
            body = f"{rng.choice(persona['openers'])}{sep}{body}"
        if persona["closers"] and rng.random() < 0.25:
            end = "." if body[-1].isalnum() else ""
            body = f"{body}{end}{sep}{rng.choice(persona['closers'])}"
        if rng.random() < persona["emoji_rate"] and not any(e in body[-3:] for e in persona["emojis"]):
            body = f"{body} {rng.choice(persona['emojis'])}"
    return body, photos, audience, caption


def _post_times(start, end, count: int, rng: random.Random) -> list:
    """``count`` momentos crecientes entre ``start`` y ``end`` con huecos irregulares."""
    gaps = [rng.expovariate(1) for _ in range(count + 1)]
    total, acc, times = sum(gaps), 0, []
    for gap in gaps[:-1]:
        acc += gap
        times.append(start + (end - start) * (acc / total))
    return times


def _weighted_sample(people: list, weights: list, k: int, rng: random.Random) -> list:
    """``k`` elementos distintos, con más probabilidad para los de más peso."""
    people, weights, picked = list(people), list(weights), []
    for _ in range(min(k, len(people))):
        i = rng.choices(range(len(people)), weights=weights)[0]
        picked.append(people.pop(i))
        weights.pop(i)
    return picked


def run(*args):
    count = int(args[0]) if args else DEFAULT_COUNT
    bots = get_bots(verbose=False)
    sync_follows(bots, verbose=False)
    rng = random.Random()
    personas = {bot.pk: data for data, bot in zip(PERSONAS, bots)}
    emojis = set(Emoji.objects.filter(is_active=True).values_list("code", flat=True))
    if not emojis:
        raise SystemExit("No hay emojis en el catálogo: corre «python manage.py migrate» primero.")
    all_emojis = sorted(emojis)
    follows = set(Follow.objects.filter(follower__in=bots).values_list("follower_id", "following_id"))

    def reaction_emoji(user):
        favorites = [code for code in personas[user.pk]["reactions"] if code in emojis]
        return rng.choice(favorites) if favorites and rng.random() < 0.8 else rng.choice(all_emojis)

    totals = Counter()
    with transaction.atomic():
        now = timezone.now()
        latest = Post.objects.order_by("-created_at").values_list("created_at", flat=True).first()
        start = now - timedelta(hours=10)
        if latest and latest > start:
            start = latest
        times = _post_times(start, now, count, rng)

        used = {bot.pk: Counter() for bot in bots}
        previous = None
        for created in times:
            # Autor: según su actividad, sin repetir al de la publicación anterior.
            candidates = [bot for bot in bots if bot != previous]
            author = rng.choices(candidates, weights=[personas[b.pk]["activity"] for b in candidates])[0]
            previous = author
            persona = personas[author.pk]

            # Idea menos usada en esta corrida; texto distinto a lo que publicó hace poco.
            recent = set(Post.objects.filter(author=author).order_by("-id").values_list("body", flat=True)[:40])
            fewest = min(used[author.pk][i] for i in range(len(persona["posts"])))
            options = [i for i in range(len(persona["posts"])) if used[author.pk][i] == fewest]
            for _ in range(8):
                index = rng.choice(options)
                body, n_photos, audience, caption = _compose(persona, persona["posts"][index], rng)
                if not body or body not in recent:
                    break
            used[author.pk][index] += 1

            files = [
                photo(rng, f"{caption} {i + 1}/{n_photos}" if n_photos > 1 else caption, name=f"foto-{i + 1}.webp")
                for i in range(n_photos)
            ]
            post = create_post(author=author, body=body, files=files, audience=audience)
            Post.objects.filter(pk=post.pk).update(created_at=created)
            totals["posts"] += 1
            totals["images"] += n_photos
            totals["followers_only"] += audience == "followers"

            # Quién puede verla (regla de la app) y quién tiene más ganas de participar.
            viewers = [bot for bot in bots if bot != author and visible_posts(bot).filter(pk=post.pk).exists()]
            weights = [3 if (bot.pk, author.pk) in follows else 1 for bot in viewers]
            if not viewers or rng.random() < 0.2:   # algunas pasan sin pena ni gloria
                totals["quiet"] += 1
                continue

            for user in _weighted_sample(viewers, weights, rng.randint(1, len(viewers)), rng):
                set_reaction(user=user, post=post, emoji_code=reaction_emoji(user))
                totals["reactions"] += 1

            n_comments = rng.choice([0, 0, 0, 1, 1, 2, 2, 3, 4])
            commenters = _weighted_sample(viewers, weights, n_comments, rng)
            moments = sorted(created + (now - created) * rng.random() for _ in commenters)
            for commenter, moment in zip(commenters, moments):
                comment = create_comment(author=commenter, post=post, body=rng.choice(personas[commenter.pk]["comments"]))
                PostComment.objects.filter(pk=comment.pk).update(created_at=moment)
                totals["comments"] += 1
                if rng.random() < 0.5:
                    set_comment_reaction(user=author, comment=comment, emoji_code=reaction_emoji(author))
                    totals["comment_reactions"] += 1

                # Respuestas: casi siempre del autor; a veces se mete alguien más al hilo.
                repliers = []
                if rng.random() < 0.4:
                    repliers.append((author, personas[author.pk]["replies"]))
                others = [bot for bot in viewers if bot != commenter]
                if others and rng.random() < 0.15:
                    other = rng.choice(others)
                    repliers.append((other, personas[other.pk]["comments"]))
                reply_at = moment
                for replier, pool in repliers:
                    reply_at = reply_at + (now - reply_at) * rng.uniform(0.05, 0.5)
                    reply = create_comment(author=replier, post=post, body=rng.choice(pool), parent_id=comment.pk)
                    PostComment.objects.filter(pk=reply.pk).update(created_at=reply_at)
                    totals["replies"] += 1
                    if replier != commenter and rng.random() < 0.3:
                        set_comment_reaction(user=commenter, comment=reply, emoji_code=reaction_emoji(commenter))
                        totals["comment_reactions"] += 1

    print(
        f"Listo: {totals['posts']} publicaciones ({totals['images']} imágenes, "
        f"{totals['followers_only']} solo seguidores, {totals['quiet']} sin interacciones), "
        f"{totals['reactions']} reacciones, {totals['comments']} comentarios, {totals['replies']} respuestas "
        f"y {totals['comment_reactions']} reacciones a comentarios."
    )
