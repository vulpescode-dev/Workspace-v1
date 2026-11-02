# Reacciones con emojis

**Estado:** implementado y probado en publicaciones (`social`). Blogs y marketplace lo reutilizarán.

## Cómo está armado

| Pieza | Dónde |
|---|---|
| Catálogo (134 emojis, elegidos por el responsable del proyecto) | `apps/catalogs/data/emojis.json` |
| Tabla del catálogo | `catalogs.Emoji` (`code`, `codepoint`, `char`, `label`, `position`, `is_active`) |
| Carga/actualización | migración `catalogs.0002_load_emojis` (primera vez), `python manage.py load_catalogs` (cambios o recuperación) y, si tras `migrate` la tabla queda vacía, carga automática (`post_migrate`) |
| Base para reacciones de cualquier app | `catalogs.BaseReaction` (abstracto: `user`, `emoji`, `created_at`, `updated_at`) |
| Reacciones a posts | `social.PostReaction` (`post` + base). **Una por persona y post** (decisión confirmada): elegir otro emoji la reemplaza |
| Archivos | `static/assets/emoji/<code>/emoji.svg` y `lottie.json` (Noto Animated Emoji) |
| Reproductor de animaciones | `static/assets/vendor/lottie/lottie_light.min.js` (lottie-web 5.12.2), se descarga solo al animar |
| Frontend | `static/assets/js/reactions.js`, plantillas `reaction_chip.html`, `emoji_picker.html`, `reactions_modal.html` |

### Reglas
- **Agregar/cambiar emojis:** editar el JSON (código, codepoint, carácter, etiqueta, orden), poner sus archivos en `static/assets/emoji/<code>/` y correr `load_catalogs`. También se puede reordenar o desactivar desde `/admin/`.
- **Quitar un emoji:** sacarlo del JSON (o desactivarlo en el admin). Queda `is_active = false`: desaparece del selector y las reacciones existentes se siguen mostrando. **No se borra** (`PROTECT`).
- El servidor rechaza emojis inexistentes o desactivados (400).
- **Un emoji por persona y post** es decisión confirmada del proyecto. Si algún día se quisiera permitir varios: cambiar la restricción de `PostReaction` a (post, user, emoji) y ajustar `services/reactions.py` y `reactions.js`.

## Experiencia (guía Emil Kowalski)

- Pastillas de 20 px con **SVG estático** + contador; la tuya resaltada en azul. Tocarla la quita; tocar otra la cambia.
- Botón «carita +» abre una **hoja inferior** (offcanvas) con la cuadrícula de 36 px. Curva tipo iOS para la hoja.
- **Animación con propósito:** el emoji que eliges se anima **una vez** en su pastilla al reaccionar (confirmación). En el selector se anima el emoji bajo el puntero (solo con mouse) o con foco del teclado. El feed no anima en bucle.
- **Optimista:** la pastilla cambia al instante y se corrige con la respuesta; si falla, se revierte y aparece un aviso.
- Pastilla nueva: entra desde `scale(0.9)` con fundido en 200 ms. Las pastillas existentes no se reordenan mientras las ves (no saltan).
- «Reducir movimiento»: nada se anima.
- «Ver todo»: modal con el resumen y la lista de quién reaccionó.

## Peso

| Recurso | Total 134 emojis | Cuándo se descarga |
|---|---|---|
| SVG estáticos | ~800 KB (≈6 KB c/u) | Los que se ven (pastillas) y los del selector al abrirlo (`loading="lazy"`) |
| Lottie JSON | ~10 MB en disco (8–235 KB c/u) | Uno a la vez, solo el que se anima |
| lottie-web light | 168 KB | La primera vez que algo se anima |

Los archivos salen del CDN oficial de Noto: `https://fonts.gstatic.com/s/e/notoemoji/latest/<codepoint>/emoji.svg` y `.../lottie.json`.

## Pendiente

- **(decidir)** Licencia de Noto Animated Emoji: no se pudo confirmar en las fuentes oficiales (el repositorio da 404). Verificar antes de producción; si es CC BY 4.0, agregar atribución.
- Caché de la API de `catalogs` (ver `docs/backlog.md`).
