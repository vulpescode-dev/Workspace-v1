from django.urls import path

from .views import (
    ListingCategoryListView, ListingDetailView, ListingImageDetailView, ListingImageFileView, ListingImagesView,
    ListingListCreateView,
)

app_name = "marketplace-api"
urlpatterns = [
    path("listings/", ListingListCreateView.as_view(), name="listing-list"),
    path("listings/<int:pk>/", ListingDetailView.as_view(), name="listing-detail"),
    path("listings/<int:pk>/images/", ListingImagesView.as_view(), name="listing-images"),
    path("images/<int:pk>/", ListingImageDetailView.as_view(), name="image-detail"),
    path("categories/", ListingCategoryListView.as_view(), name="category-list"),
    path("images/<int:pk>/file/", ListingImageFileView.as_view(), name="image-file"),
]
