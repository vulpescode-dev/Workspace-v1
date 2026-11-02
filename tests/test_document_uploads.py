"""Pruebas de ``check_document_upload``: lista permitida por contenido para adjuntos de tipo documento."""
import io
import zipfile

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from apps.core import uploads

PDF = b"%PDF-1.7\n1 0 obj << /Type /Catalog >> endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n"
CONTENT_TYPES = b'<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>'


def raw_file(name, content, content_type="application/octet-stream"):
    return SimpleUploadedFile(name, content, content_type=content_type)


def office_file(name, main_part, extra_parts=(), content_types=CONTENT_TYPES):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as package:
        package.writestr("[Content_Types].xml", content_types)
        package.writestr(main_part, "<xml/>")
        for part in extra_parts:
            package.writestr(part, b"\x00\x01")
    return raw_file(name, buffer.getvalue())


def image_file(name, fmt):
    buffer = io.BytesIO()
    Image.new("RGB", (30, 20), (0, 102, 204)).save(buffer, fmt)
    return raw_file(name, buffer.getvalue())


class DocumentValidationTests(SimpleTestCase):
    def assert_rejected(self, upload):
        with self.assertRaises(ValidationError):
            uploads.check_document_upload(upload)

    def test_accepts_allowed_types_by_content(self):
        cases = [
            (raw_file("informe.pdf", PDF), ".pdf", "application/pdf"),
            (office_file("carta.docx", "word/document.xml"), ".docx", None),
            (office_file("ventas.xlsx", "xl/workbook.xml"), ".xlsx", None),
            (office_file("junta.pptx", "ppt/presentation.xml"), ".pptx", None),
            (image_file("captura.png", "PNG"), ".png", "image/png"),
            (image_file("foto.jpg", "JPEG"), ".jpg", "image/jpeg"),
            (image_file("foto.webp", "WEBP"), ".webp", "image/webp"),
            (raw_file("datos.csv", "nombre,área\nAna,TI\n".encode("utf-8")), ".csv", "text/csv"),
            (raw_file("excel.csv", "nombre,área\nAna,TI\n".encode("cp1252")), ".csv", "text/csv"),
            (raw_file("notas.txt", b"Hola"), ".txt", "text/plain"),
        ]
        for upload, extension, content_type in cases:
            with self.subTest(upload.name):
                info = uploads.check_document_upload(upload)
                self.assertEqual(info.extension, extension)
                if content_type:
                    self.assertEqual(info.content_type, content_type)

    def test_extension_comes_from_content_not_name(self):
        self.assertEqual(uploads.check_document_upload(raw_file("engaño.txt", PDF)).extension, ".pdf")

    def test_rejects_executables_scripts_and_markup(self):
        for upload in (
            raw_file("virus.exe", b"MZ\x90\x00" + b"\x00" * 100),
            raw_file("virus.pdf", b"MZ\x90\x00" + b"\x00" * 100),
            raw_file("script.txt", b"#!/bin/sh\nrm -rf /\n"),
            raw_file("binario.txt", b"abc\x00def"),
            raw_file("x.js", b"alert(1)"),
            raw_file("page.html", b"<html><script>alert(1)</script></html>"),
            raw_file("x.svg", b"<svg xmlns='http://www.w3.org/2000/svg'/>"),
            raw_file("vacio.pdf", b""),
        ):
            with self.subTest(upload.name):
                self.assert_rejected(upload)

    def test_rejects_active_or_broken_pdfs(self):
        self.assert_rejected(raw_file("js.pdf", PDF.replace(b"/Catalog", b"/Catalog /OpenAction << /S /JavaScript >>")))
        self.assert_rejected(raw_file("launch.pdf", PDF.replace(b"/Catalog", b"/Catalog /AA << /S /Launch >>")))
        self.assert_rejected(raw_file("adjunto.pdf", PDF.replace(b"/Catalog", b"/Catalog /Names << /EmbeddedFiles 2 0 R >>")))
        self.assert_rejected(raw_file("cortado.pdf", PDF[:-6]))

    def test_rejects_macros_activex_ole_and_plain_zips(self):
        self.assert_rejected(office_file("macro.xlsx", "xl/workbook.xml", ["xl/vbaProject.bin"]))
        self.assert_rejected(office_file("macro.docm", "word/document.xml", content_types=CONTENT_TYPES.replace(
            b"/>", b'><Override ContentType="application/vnd.ms-word.document.macroEnabled.main+xml"/></Types>')))
        self.assert_rejected(office_file("activex.docx", "word/document.xml", ["word/activeX/activeX1.xml"]))
        self.assert_rejected(office_file("ole.pptx", "ppt/presentation.xml", ["ppt/embeddings/oleObject1.bin"]))
        self.assert_rejected(office_file("exe.docx", "word/document.xml", ["word/media/setup.exe"]))
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as package:
            package.writestr("leeme.txt", "hola")
        self.assert_rejected(raw_file("archivo.zip", buffer.getvalue()))
        self.assert_rejected(raw_file("roto.docx", b"PK\x03\x04" + b"\x00" * 100))

    def test_size_limit(self):
        self.assert_rejected(raw_file("grande.txt", b"a" * (uploads.DOCUMENT_MAX_BYTES + 1)))
