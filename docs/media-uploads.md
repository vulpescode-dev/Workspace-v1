# Media en publicaciones (imágenes y videos)

**Estado:** implementado y probado. Las publicaciones aceptan **solo imágenes y videos**; documentos no (decisión del proyecto).

## Flujo

1. **Navegador** (`static/assets/js/workspace.js` → `Workspace.procesarAWebP(file, { maxSide: 2048, quality: 0.82 })`):
   - Toda imagen (JPEG, PNG, HEIC si el navegador la decodifica, etc.) se convierte a **WebP**; si ya es WebP y no excede 2048 px, se usa tal cual.
   - Reduce a 2048 px por el lado mayor, respeta la orientación EXIF y **elimina los metadatos** (p. ej. GPS).
   - Si el navegador no puede codificar WebP, la imagen se rechaza con un mensaje (no se sube otro formato).
   - Los videos no se procesan; solo se revisa tipo (MP4/MOV/WebM) y tamaño.
2. **Servidor** (`apps/core/uploads.py` → `check_media_upload`): **lista permitida por contenido real**.
   - Imagen: firma `RIFF…WEBP` + Pillow la decodifica y confirma `format == "WEBP"`; máx. 10 MB y 4096 px por lado.
   - Video: firma de contenedor MP4/MOV (`ftyp` + marca conocida) o WebM (EBML + `webm`); máx. 100 MB.
   - Todo lo demás se rechaza: `.exe`, `.php`, scripts, HTML, SVG, PDF, ZIP… aunque se renombren a `.webp` o manden un Content-Type falso.
   - Si **un** archivo falla, no se crea la publicación (todo o nada). Máx. 10 archivos por post.
3. **Guardado** (`apps/social/services/posts.py`): `media/social/posts/<post_id>/<attachment_id>.<ext>`. El nombre original solo queda como dato (`original_name`), nunca en disco.
4. **Entrega** (`GET /api/social/attachments/<id>/file/`): solo si el post es visible para quien lo pide. Las rutas `/media/` no se exponen (los nombres son secuenciales). Cabeceras `X-Content-Type-Options: nosniff`, `Content-Disposition: inline`, `Cache-Control: private`.
5. Al borrar un adjunto o su publicación, el archivo se borra del disco.

## Interfaz

- Composer: botón «Foto / Video», miniaturas con spinner mientras se convierte, quitar cada una, contador `n / 10`, barra de progreso de subida.
- Tarjeta: media a todo el ancho; 1 = proporción propia (acotada), 2 = lado a lado, 3 = una grande + dos, 4+ = cuadrícula con «+N». Videos con controles nativos.

## Pendiente

Ver `docs/backlog.md` (visor a pantalla completa, prueba de video en dispositivo real, entrega por el servidor web en producción, compresión de video).
