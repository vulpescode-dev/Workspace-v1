from django.urls import path

from .views import (
    ArticleCommentListCreateView, ArticleCoverView, ArticleDetailView, ArticleListCreateView, ArticleReactionListView,
    ArticleReactionView, BlogPermissionsView, CategoryListView, CommentDetailView,
)

app_name = "blog-api"
urlpatterns = [
    path("articles/", ArticleListCreateView.as_view(), name="article-list"),
    path("articles/<int:pk>/", ArticleDetailView.as_view(), name="article-detail"),
    path("articles/<int:pk>/cover/", ArticleCoverView.as_view(), name="article-cover"),
    path("articles/<int:pk>/reaction/", ArticleReactionView.as_view(), name="article-reaction"),
    path("articles/<int:pk>/reactions/", ArticleReactionListView.as_view(), name="article-reaction-list"),
    path("articles/<int:pk>/comments/", ArticleCommentListCreateView.as_view(), name="article-comment-list"),
    path("comments/<int:pk>/", CommentDetailView.as_view(), name="comment-detail"),
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("permissions/", BlogPermissionsView.as_view(), name="permissions"),
]
