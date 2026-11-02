from django.urls import path

from . import views

app_name = "social"
urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
    path("posts/<int:pk>/", views.post_detail, name="post-detail"),
]
