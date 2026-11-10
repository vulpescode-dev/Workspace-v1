"""Paginación de la API preparada para páginas inexistentes.

DRF responde 404 «Página inválida» sin más datos. Aquí, si piden una página que no existe
(``?page=999``, ``?page=0``, ``?page=abc``), se responde 404 con un mensaje claro y lo necesario
para recuperarse: cuántos resultados y cuántas páginas hay. La página 1 siempre es válida,
aunque no haya resultados.
"""
from django.core.paginator import InvalidPage
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import exception_handler


class PageNotFound(NotFound):
    """404 de paginación. ``extra`` se agrega a la respuesta tal cual (números como números):
    DRF convierte a texto todo lo que va dentro de ``detail``, por eso no va ahí."""

    def __init__(self, page, count: int, total_pages: int):
        super().__init__(f"La página «{page}» no existe.")
        self.extra = {"page": str(page), "count": count, "total_pages": total_pages}


def api_exception_handler(exc, context):
    """Manejador de errores de la API (``REST_FRAMEWORK["EXCEPTION_HANDLER"]``): el de DRF + datos extra."""
    response = exception_handler(exc, context)
    if response is not None and isinstance(exc, PageNotFound):
        response.data.update(exc.extra)
    return response


class SafePageNumberPagination(PageNumberPagination):
    """Paginación de toda la API (``DEFAULT_PAGINATION_CLASS``).

    25 por página (``PAGE_SIZE``). Se puede pedir menos con ``?page_size=`` (p. ej. 5, 10 o 15);
    más de 25 se limita a 25 y un valor inválido (``0``, ``abc``) usa el de siempre.
    """

    page_size_query_param = "page_size"
    max_page_size = 25

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        paginator = self.django_paginator_class(queryset, self.get_page_size(request))
        page_number = request.query_params.get(self.page_query_param) or 1
        try:
            self.page = paginator.page(page_number)
        except InvalidPage:
            raise PageNotFound(page_number, paginator.count, paginator.num_pages) from None
        return list(self.page)

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "page": self.page.number,
            "total_pages": self.page.paginator.num_pages,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data,
        })
