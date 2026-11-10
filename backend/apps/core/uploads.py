"""Validación de archivos subidos por usuarios (compartida por las apps que acepten media).

Regla: **lista permitida**. Solo entran los tipos de esta lista y se comprueba el
contenido real del archivo (firma / decodificación), nunca la extensión ni el
Content-Type que manda el navegador. Todo lo demás (.exe, .php, scripts, HTML,
SVG, documentos…) se rechaza porque no coincide con ninguna firma permitida.

- Imágenes: solo WebP. El navegador convierte antes de subir (``Workspace.procesarAWebP``);
  aquí se decodifica con Pillow para confirmar que es una imagen WebP real y de tamaño razonable.
- Videos: MP4, MOV (QuickTime) y WebM, por su firma de contenedor.

Documentos (``check_document_upload``: tickets, documentos, formularios): PDF, Word/Excel/PowerPoint
modernos sin macros, CSV/TXT e imágenes PNG/JPEG/WebP. Ver la docstring de esa función.

El archivo se guarda con un nombre generado por el servidor (``<id>.<ext>``), así que el
nombre original del usuario nunca llega al disco.
"""
import re
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath

from django.core.exceptions import ValidationError
from PIL import Image

MB = 1024 * 1024
IMAGE_MAX_BYTES = 10 * MB
VIDEO_MAX_BYTES = 100 * MB
DOCUMENT_MAX_BYTES = 20 * MB
IMAGE_MAX_SIDE = 4096           # el navegador reduce a 2048; esto es el tope del servidor
IMAGE_MAX_PIXELS = IMAGE_MAX_SIDE * IMAGE_MAX_SIDE

KIND_IMAGE = "image"
KIND_VIDEO = "video"
KIND_DOCUMENT = "document"


@dataclass(frozen=True)
class CheckedUpload:
    kind: str           # "image" | "video" | "document"
    extension: str      # con punto: ".webp", ".mp4", ".pdf", ".xlsx"…
    content_type: str
    size: int
    width: int | None = None
    height: int | None = None


def _head(upload, length: int = 64) -> bytes:
    upload.seek(0)
    data = upload.read(length)
    upload.seek(0)
    return data


def _video_type(head: bytes) -> tuple[str, str] | None:
    # MP4 / MOV: caja "ftyp" en los bytes 4–8 y una marca (brand) conocida.
    if head[4:8] == b"ftyp":
        brand = head[8:12]
        if brand == b"qt  ":
            return ".mov", "video/quicktime"
        if brand in {b"isom", b"iso2", b"iso4", b"iso5", b"iso6", b"mp41", b"mp42", b"avc1", b"M4V ", b"dash"}:
            return ".mp4", "video/mp4"
        return None
    # WebM (Matroska/EBML) con DocType "webm".
    if head[:4] == b"\x1a\x45\xdf\xa3" and b"webm" in head:
        return ".webm", "video/webm"
    return None


def _check_image(upload) -> CheckedUpload:
    if upload.size > IMAGE_MAX_BYTES:
        raise ValidationError(f"La imagen supera {IMAGE_MAX_BYTES // MB} MB.")
    try:
        with Image.open(upload) as image:
            if image.format != "WEBP":
                raise ValidationError("Las imágenes deben llegar en WebP.")
            width, height = image.size
            if width * height > IMAGE_MAX_PIXELS or max(width, height) > IMAGE_MAX_SIDE:
                raise ValidationError(f"La imagen es demasiado grande (máx. {IMAGE_MAX_SIDE} px por lado).")
            image.verify()
    except ValidationError:
        raise
    except Exception as exc:  # Pillow lanza varios tipos ante archivos corruptos o falsos
        raise ValidationError("El archivo no es una imagen válida.") from exc
    finally:
        upload.seek(0)
    return CheckedUpload(KIND_IMAGE, ".webp", "image/webp", upload.size, width, height)


def check_media_upload(upload) -> CheckedUpload:
    """Valida un archivo de imagen o video. Lanza ``ValidationError`` si no está permitido."""
    if not upload or not upload.size:
        raise ValidationError("El archivo está vacío.")
    head = _head(upload)
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return _check_image(upload)
    video = _video_type(head)
    if video:
        if upload.size > VIDEO_MAX_BYTES:
            raise ValidationError(f"El video supera {VIDEO_MAX_BYTES // MB} MB.")
        extension, content_type = video
        return CheckedUpload(KIND_VIDEO, extension, content_type, upload.size)
    raise ValidationError("Tipo de archivo no permitido. Solo imágenes (WebP) y videos MP4, MOV o WebM.")


# --- Documentos -------------------------------------------------------------------------------

DOCUMENT_IMAGE_TYPES = {"WEBP": (".webp", "image/webp"), "PNG": (".png", "image/png"), "JPEG": (".jpg", "image/jpeg")}
OOXML_TYPES = {   # parte principal del paquete → tipo
    "word/document.xml": (".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    "xl/workbook.xml": (".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    "ppt/presentation.xml": (".pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
}
TEXT_TYPES = {".csv": "text/csv", ".txt": "text/plain"}
ZIP_MAX_ENTRIES = 5000
ZIP_MAX_UNCOMPRESSED = 200 * MB          # contra «bombas zip»
# Partes de Office que pueden ejecutar código: macros (VBA), controles ActiveX y objetos OLE incrustados.
OOXML_BLOCKED_PARTS = re.compile(r"(?:^|/)(?:vbaproject\.bin|vbadata\.xml)$|(?:^|/)activex/|(?:^|/)embeddings/[^/]*\.bin$")
EXECUTABLE_EXTENSIONS = {
    ".exe", ".dll", ".com", ".scr", ".msi", ".bat", ".cmd", ".ps1", ".vbs", ".vbe", ".js", ".jse", ".wsf", ".hta",
    ".jar", ".sh", ".lnk",
}
# Acciones activas de PDF (JavaScript, abrir programas, archivos incrustados). Revisión de apoyo: los
# objetos comprimidos no se inspeccionan, por eso en producción se suma antivirus (ver backlog).
PDF_ACTIVE_CONTENT = re.compile(rb"/(?:JavaScript|JS|Launch|EmbeddedFiles?|RichMedia)(?![A-Za-z0-9])")


def _document_image(upload, image_format: str) -> CheckedUpload:
    try:
        with Image.open(upload) as image:
            if image.format != image_format:
                raise ValidationError("El archivo no es una imagen válida.")
            width, height = image.size
            if width * height > IMAGE_MAX_PIXELS or max(width, height) > IMAGE_MAX_SIDE:
                raise ValidationError(f"La imagen es demasiado grande (máx. {IMAGE_MAX_SIDE} px por lado).")
            image.verify()
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError("El archivo no es una imagen válida.") from exc
    finally:
        upload.seek(0)
    extension, content_type = DOCUMENT_IMAGE_TYPES[image_format]
    return CheckedUpload(KIND_IMAGE, extension, content_type, upload.size, width, height)


def _check_pdf(upload) -> CheckedUpload:
    upload.seek(0)
    data = upload.read()
    upload.seek(0)
    if b"%%EOF" not in data[-2048:]:
        raise ValidationError("El PDF está incompleto o dañado.")
    if PDF_ACTIVE_CONTENT.search(data):
        raise ValidationError("El PDF trae contenido activo (JavaScript o archivos incrustados) y no se permite.")
    return CheckedUpload(KIND_DOCUMENT, ".pdf", "application/pdf", upload.size)


def _check_ooxml(upload) -> CheckedUpload:
    try:
        with zipfile.ZipFile(upload) as package:
            entries = package.infolist()
            names = {entry.filename for entry in entries}
            if len(entries) > ZIP_MAX_ENTRIES or sum(entry.file_size for entry in entries) > ZIP_MAX_UNCOMPRESSED:
                raise ValidationError("El documento es demasiado grande al descomprimirse.")
            if "[Content_Types].xml" not in names:
                raise ValidationError("Solo se aceptan documentos de Word, Excel o PowerPoint (no archivos .zip).")
            content_types = package.read("[Content_Types].xml").lower()
    except ValidationError:
        raise
    except Exception as exc:  # zip dañado, cifrado o falso
        raise ValidationError("El documento está dañado o protegido con contraseña.") from exc
    finally:
        upload.seek(0)
    for name in names:
        lowered = name.lower()
        if OOXML_BLOCKED_PARTS.search(lowered) or PurePosixPath(lowered).suffix in EXECUTABLE_EXTENSIONS:
            raise ValidationError("El documento trae macros u objetos ejecutables y no se permite.")
    if b"macroenabled" in content_types:
        raise ValidationError("Los documentos con macros (.docm, .xlsm, .pptm) no se permiten.")
    for part, (extension, content_type) in OOXML_TYPES.items():
        if part in names:
            return CheckedUpload(KIND_DOCUMENT, extension, content_type, upload.size)
    raise ValidationError("Solo se aceptan documentos de Word, Excel o PowerPoint.")


def _check_text(upload, extension: str) -> CheckedUpload:
    upload.seek(0)
    data = upload.read()
    upload.seek(0)
    if b"\x00" in data or data.startswith(b"#!"):
        raise ValidationError("El archivo de texto no es válido.")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        try:
            data.decode("cp1252")   # CSV exportado por Excel en Windows (español)
        except UnicodeDecodeError:
            raise ValidationError("El archivo de texto no es válido.") from None
    return CheckedUpload(KIND_DOCUMENT, extension, TEXT_TYPES[extension], upload.size)


def check_document_upload(upload) -> CheckedUpload:
    """Valida un adjunto de tipo documento. Lanza ``ValidationError`` si no está permitido.

    Lista permitida por contenido real (máx. ``DOCUMENT_MAX_BYTES``):

    - PDF (``%PDF-``), sin JavaScript, acciones de abrir programas ni archivos incrustados.
    - Word, Excel y PowerPoint modernos (``.docx``, ``.xlsx``, ``.pptx``: paquete zip con su parte
      principal), sin macros, ActiveX ni objetos OLE. Los formatos viejos ``.doc``/``.xls``/``.ppt``
      no se aceptan (pueden traer macros); se piden guardados como versión moderna.
    - Imágenes PNG, JPEG y WebP que Pillow decodifica (capturas de pantalla).
    - Texto: ``.csv`` y ``.txt`` (por la extensión, porque no tienen firma) en UTF-8 o Windows-1252,
      sin bytes binarios.

    Todo lo demás se rechaza: ejecutables, scripts, HTML, SVG, zip, etc., aunque se renombren.
    """
    if not upload or not upload.size:
        raise ValidationError("El archivo está vacío.")
    if upload.size > DOCUMENT_MAX_BYTES:
        raise ValidationError(f"El archivo supera {DOCUMENT_MAX_BYTES // MB} MB.")
    head = _head(upload)
    if head.startswith(b"%PDF-"):
        return _check_pdf(upload)
    if head.startswith(b"PK\x03\x04"):
        return _check_ooxml(upload)
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return _document_image(upload, "WEBP")
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return _document_image(upload, "PNG")
    if head.startswith(b"\xff\xd8\xff"):
        return _document_image(upload, "JPEG")
    extension = PurePosixPath((getattr(upload, "name", "") or "").lower()).suffix
    if extension in TEXT_TYPES:
        return _check_text(upload, extension)
    raise ValidationError("Tipo de archivo no permitido. Se aceptan PDF, Word, Excel, PowerPoint, CSV, TXT e imágenes.")
