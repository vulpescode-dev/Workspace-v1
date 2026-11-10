"""DATOS DE DEMOSTRACIÓN de la portada (accesos rápidos).

Las publicaciones y los avisos ya son reales (API); lo de aquí se reemplaza conforme
se implementen la búsqueda y los demás módulos. ``color`` es un color de
Bootstrap (primary, secondary, success, danger, warning, info). Cada acceso lleva ``href``
(nombre de URL de Django) o ``soon`` (aún no existe).
"""

DEMO_CATEGORIES = [
    {"icon": "bx-folder-open", "label": "Documentos", "color": "primary", "href": "documents"},
    {"icon": "bx-list-check", "label": "Formularios", "color": "success", "href": "forms"},
    {"icon": "bx-bell", "label": "Avisos", "color": "danger", "href": "notifications"},
    {"icon": "bx-group", "label": "Directorio", "color": "secondary", "href": "people"},
]
