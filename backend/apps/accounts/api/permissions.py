"""Acceso por sección para las vistas de la API (permisos de negocio, no los de Django).

Cada sección se abre con su permiso ``view``; también entra quien tiene un permiso que ya implica verla
(``.view.all``, crear, administrar, atender…): no tendría sentido poder publicar y no ver la sección.
El superusuario entra siempre (``has_permission``). Sin acceso, la API responde 403.

Uso: ``permission_classes = [IsAuthenticated, SOCIAL_POSTS]``.
"""
from rest_framework.permissions import BasePermission

from apps.accounts.services.permissions import has_permission


def section(name: str, *codenames: str) -> type[BasePermission]:
    """Clase de permiso: deja pasar si el usuario tiene cualquiera de ``codenames``."""

    class SectionAccess(BasePermission):
        message = f"No tienes acceso a {name}."

        def has_permission(self, request, view):
            return any(has_permission(request.user, code) for code in codenames)

    SectionAccess.__name__ = SectionAccess.__qualname__ = f"SectionAccess[{codenames[0]}]"
    return SectionAccess


PEOPLE = section("Personas", "accounts.users.view", "accounts.users.view.all")
DEPARTMENTS = section("los departamentos", "org.departments.view")
ORG_CHART = section("el organigrama", "org.chart.view")
SOCIAL_POSTS = section("las publicaciones", "social.posts.view", "social.posts.view.all", "social.posts.create")
STORIES = section("los estados", "social.stories.view", "social.stories.create")
BLOG = section("Noticias", "blog.articles.view", "blog.articles.view.all", "blog.articles.create")
DOCUMENTS = section(
    "Documentos", "documents.documents.view", "documents.documents.view.all", "documents.documents.create",
    "documents.documents.manage",
)
FORMS = section("Formularios", "forms.forms.view", "forms.forms.view.all", "forms.forms.create")
HELPDESK = section(
    "la Mesa de ayuda", "helpdesk.tickets.view", "helpdesk.tickets.view.all", "helpdesk.tickets.create",
    "helpdesk.tickets.attend",
)
MARKETPLACE = section("el Marketplace", "marketplace.listings.view", "marketplace.listings.create")
