from django.urls import path

from .views import (
    DocumentCategoryListView, DocumentDetailView, DocumentListCreateView, DocumentsMeView, DocumentVersionCreateView,
    DocumentVersionFileView, DocumentVersionRestoreView,
)

app_name = "documents-api"
urlpatterns = [
    path("me/", DocumentsMeView.as_view(), name="me"),
    path("categories/", DocumentCategoryListView.as_view(), name="category-list"),
    path("documents/", DocumentListCreateView.as_view(), name="document-list"),
    path("documents/<int:pk>/", DocumentDetailView.as_view(), name="document-detail"),
    path("documents/<int:pk>/versions/", DocumentVersionCreateView.as_view(), name="document-versions"),
    path("documents/<int:pk>/versions/<int:version_pk>/restore/", DocumentVersionRestoreView.as_view(),
         name="version-restore"),
    path("versions/<int:pk>/file/", DocumentVersionFileView.as_view(), name="version-file"),
]
