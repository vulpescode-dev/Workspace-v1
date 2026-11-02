from django.urls import path

from .views import BirthdaysView, DirectoryView, MyProfileImageView, MyProfileView, ProfileView, UserImageView

app_name = "accounts-api"
urlpatterns = [
    path("me/", MyProfileView.as_view(), name="me"),
    path("me/avatar/", MyProfileImageView.as_view(field="avatar"), name="me-avatar"),
    path("users/", DirectoryView.as_view(), name="user-list"),
    path("birthdays/", BirthdaysView.as_view(), name="birthdays"),
    path("users/<int:pk>/", ProfileView.as_view(), name="user-profile"),
    path("users/<int:pk>/avatar/", UserImageView.as_view(field="avatar"), name="user-avatar"),
]
