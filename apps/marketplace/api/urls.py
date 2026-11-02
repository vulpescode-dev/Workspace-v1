from django.urls import path

from .views import ListingCategoryListView, ListingDetailView, ListingImageFileView, ListingListCreateView

app_name = "marketplace-api"
urlpatterns = [
    path("listings/", ListingListCreateView.as_view(), name="listing-list"),
    path("listings/<int:pk>/", ListingDetailView.as_view(), name="listing-detail"),
    path("categories/", ListingCategoryListView.as_view(), name="category-list"),
    path("images/<int:pk>/file/", ListingImageFileView.as_view(), name="image-file"),
]
