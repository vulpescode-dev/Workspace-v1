from django.urls import path

from .views import (
    MarkAllReadView, NotificationDetailView, NotificationListView, PushConfigView, PushSubscriptionDetailView,
    PushSubscriptionListView, PushUnsubscribeView, UnreadCountView,
)

app_name = "notifications-api"
urlpatterns = [
    path("", NotificationListView.as_view(), name="list"),
    path("<int:pk>/", NotificationDetailView.as_view(), name="detail"),
    path("unread-count/", UnreadCountView.as_view(), name="unread-count"),
    path("read-all/", MarkAllReadView.as_view(), name="read-all"),
    path("push/config/", PushConfigView.as_view(), name="push-config"),
    path("push/subscriptions/", PushSubscriptionListView.as_view(), name="push-subscription-list"),
    path("push/subscriptions/<int:pk>/", PushSubscriptionDetailView.as_view(), name="push-subscription-detail"),
    path("push/unsubscribe/", PushUnsubscribeView.as_view(), name="push-unsubscribe"),
]
