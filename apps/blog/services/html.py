"""Limpieza del HTML de los artículos (lo produce un editor enriquecido, p. ej. CKEditor).

Lista permitida: solo se conservan las etiquetas y atributos que un editor de texto genera
(títulos, listas, enlaces, imágenes, tablas, citas, código). Todo lo demás —``<script>``,
``<iframe>``, ``on*=``, ``javascript:``, estilos arbitrarios— se elimina. Se aplica al guardar el
modelo, así que la base de datos nunca contiene HTML peligroso, venga de donde venga.
"""
import nh3

ALLOWED_TAGS = {
    "p", "br", "hr", "h2", "h3", "h4", "strong", "b", "em", "i", "u", "s", "sub", "sup", "mark", "span",
    "a", "ul", "ol", "li", "blockquote", "pre", "code",
    "figure", "figcaption", "img",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption", "colgroup", "col",
}
ALLOWED_ATTRIBUTES = {
    "*": {"style"},
    "a": {"href", "title", "target"},
    "img": {"src", "alt", "width", "height"},
    "th": {"colspan", "rowspan", "scope"},
    "td": {"colspan", "rowspan"},
    "col": {"span"},
    "ol": {"start", "reversed"},
}
# Solo las clases que usa CKEditor para acomodar imágenes y tablas.
ALLOWED_CLASSES = {"figure": {"image", "image_resized", "image-style-side", "image-style-align-left",
                              "image-style-align-right", "image-style-align-center", "table"}}
# De ``style`` solo sobreviven estas propiedades (alineación y tamaño de imagen).
ALLOWED_STYLES = {"text-align", "width"}
URL_SCHEMES = {"http", "https", "mailto"}


def clean_article_html(html: str) -> str:
    return nh3.clean(
        html or "",
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        allowed_classes=ALLOWED_CLASSES,
        filter_style_properties=ALLOWED_STYLES,
        url_schemes=URL_SCHEMES,
        link_rel="noopener noreferrer",
    ).strip()
