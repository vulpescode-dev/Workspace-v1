# Reacciones con emojis

**Estado:** implementado y probado en publicaciones (`social`). Blogs y marketplace lo reutilizarán.

## Cómo está armado

| Pieza | Dónde |
|---|---|
| Catálogo (134 emojis, elegidos por el responsable del proyecto) | `backend/apps/catalogs/data/emojis.json` |
| Tabla del catálogo | `catalogs.Emoji` (`code`, `codepoint`, `char`, `label`, `position`, `is_active`) |
| Carga/actualización | migración `catalogs.0002_load_emojis` (primera vez), `python manage.py load_catalogs` (cambios o recuperación) y, si tras `migrate` la tabla queda vacía, carga automática (`post_migrate`) |
| Base para reacciones de cualquier app | `catalogs.BaseReaction` (abstracto: `user`, `emoji`, `created_at`, `updated_at`) |
| Reacciones a posts | `social.PostReaction` (`post` + base). **Una por persona y post** (decisión confirmada): elegir otro emoji la reemplaza |
| Archivos | `backend/static/assets/emoji/<code>/emoji.svg` y `lottie.json` (Noto Animated Emoji); la API entrega sus URLs (`svg_url`, `lottie_url`) |
| Reproductor de animaciones | `lottie-web` 5.12.2 (versión **SVG con expresiones**; la *light* dejaba en blanco emojis como «Heart hands») desde npm, en su propio archivo (~243 KB): se descarga la primera vez que algo se anima (`frontend/src/features/reactions/utils/lottie.ts`) |
| Frontend | `frontend/src/features/reactions/`: `AnimatedEmoji`, `ReactionSheet` (hoja inferior), `ReactionSummaryChips` (pastillas), `ReactionListSheet` («Ver todo») |

### Reglas
- **Agregar/cambiar emojis:** editar el JSON (código, codepoint, carácter, etiqueta, orden), poner sus archivos en `backend/static/assets/emoji/<code>/` y correr `load_catalogs`. También se puede reordenar o desactivar desde `/admin/`.
- **Quitar un emoji:** sacarlo del JSON (o desactivarlo en el admin). Queda `is_active = false`: desaparece del selector y las reacciones existentes se siguen mostrando. **No se borra** (`PROTECT`).
- El servidor rechaza emojis inexistentes o desactivados (400).
- **Un emoji por persona y post** es decisión confirmada del proyecto. Si algún día se quisiera permitir varios: cambiar la restricción de `PostReaction` a (post, user, emoji) y ajustar `services/reactions.py` y el frontend.

## Experiencia (guía Emil Kowalski)

**Los emojis animados son parte esencial de la experiencia** (decisión del responsable del proyecto): no se
reemplazan por emojis quietos.

- Pastillas de 20 px con el SVG + contador; la tuya resaltada en azul. Tocarla la quita; tocar otra la cambia.
- Botón «carita +» (Reaccionar) abre una **hoja inferior a todo el ancho** en cualquier pantalla (Vaul,
  curva tipo iOS, se cierra arrastrando). En pantallas grandes la cuadrícula usa el mismo contenedor que
  la página y caben los 134 emojis sin desplazarse. Desde los comentarios se abre apilada sobre su hoja.
- Cuadrícula de 36 px. **Todos los emojis que se ven en la hoja se animan en bucle**; al desplazar,
  los que salen de pantalla se detienen y liberan memoria (`IntersectionObserver`).
- El emoji que eliges se anima **una vez** en su pastilla al reaccionar (confirmación). Con mouse, la pastilla
  señalada también se anima.
- El feed no anima en bucle: las pastillas solo se animan al elegir o al señalar.
- **Optimista:** la pastilla cambia al instante y se corrige con la respuesta; si falla, se revierte y avisa.
- Pastilla nueva: entra desde `scale(0.9)` con fundido en 200 ms. Las existentes **no se reordenan** mientras
  las ves (se conserva el orden y las nuevas van al final).
- «Reducir movimiento»: nada se anima (se ven los SVG).
- «Ver todo»: hoja con filtro por emoji y la lista de quién reaccionó.
- Los comentarios usan las mismas pastillas y la misma hoja.

## Peso

| Recurso | Total 134 emojis | Cuándo se descarga |
|---|---|---|
| SVG estáticos | ~800 KB (≈6 KB c/u) | Los que se ven (pastillas) y los del selector al abrirlo (`loading="lazy"`) |
| Lottie JSON | ~10 MB en disco (8–235 KB c/u) | Solo los que se animan (los visibles en la hoja, ~20–30 a la vez); se guardan en memoria para no volver a pedirlos |
| lottie-web SVG | 243 KB (64 KB gzip) | La primera vez que algo se anima |

Los archivos salen del CDN oficial de Noto: `https://fonts.gstatic.com/s/e/notoemoji/latest/<codepoint>/emoji.svg` y `.../lottie.json`.

## Pendiente

- **(decidir)** Licencia de Noto Animated Emoji: no se pudo confirmar en las fuentes oficiales (el repositorio da 404). Verificar antes de producción; si es CC BY 4.0, agregar atribución.
- Caché de la API de `catalogs` (ver `docs/checklist.md`).
