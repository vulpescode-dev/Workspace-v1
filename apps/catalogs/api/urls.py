from django.urls import path

from .views import EmojiListView

app_name = "catalogs-api"
urlpatterns = [
    path("emojis/", EmojiListView.as_view(), name="emoji-list"),
]
