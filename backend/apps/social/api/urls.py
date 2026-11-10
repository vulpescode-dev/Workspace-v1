from django.urls import path

from .views import (
    AttachmentFileView, CommentDetailView, CommentReactionView, FollowersListView, FollowingListView, FollowSuggestionsView,
    FollowView,
    PhotoListView, PostCommentListCreateView, PostDetailView, PostListCreateView, PostReactionListView,
    PostReactionView, StoryDetailView, StoryFileView, StoryListCreateView, StorySeenView, StoryViewersView,
)

app_name = "social-api"
urlpatterns = [
    path("posts/", PostListCreateView.as_view(), name="post-list"),
    path("posts/<int:pk>/", PostDetailView.as_view(), name="post-detail"),
    path("posts/<int:pk>/reaction/", PostReactionView.as_view(), name="post-reaction"),
    path("posts/<int:pk>/reactions/", PostReactionListView.as_view(), name="post-reaction-list"),
    path("posts/<int:pk>/comments/", PostCommentListCreateView.as_view(), name="post-comment-list"),
    path("comments/<int:pk>/", CommentDetailView.as_view(), name="comment-detail"),
    path("comments/<int:pk>/reaction/", CommentReactionView.as_view(), name="comment-reaction"),
    path("photos/", PhotoListView.as_view(), name="photo-list"),
    path("follows/<int:pk>/", FollowView.as_view(), name="follow"),
    path("follows/suggestions/", FollowSuggestionsView.as_view(), name="follow-suggestions"),
    path("users/<int:pk>/followers/", FollowersListView.as_view(), name="user-followers"),
    path("users/<int:pk>/following/", FollowingListView.as_view(), name="user-following"),
    path("attachments/<int:pk>/file/", AttachmentFileView.as_view(), name="attachment-file"),
    path("stories/", StoryListCreateView.as_view(), name="story-list"),
    path("stories/<int:pk>/", StoryDetailView.as_view(), name="story-detail"),
    path("stories/<int:pk>/seen/", StorySeenView.as_view(), name="story-seen"),
    path("stories/<int:pk>/viewers/", StoryViewersView.as_view(), name="story-viewers"),
    path("stories/<int:pk>/file/", StoryFileView.as_view(), name="story-file"),
]
