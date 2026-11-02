from django.urls import path

from .views import (
    HelpdeskMeView, TicketAgentsView, TicketAttachmentFileView, TicketCategoryListView, TicketCommentCreateView,
    TicketDetailView, TicketListCreateView,
)

app_name = "helpdesk-api"
urlpatterns = [
    path("me/", HelpdeskMeView.as_view(), name="me"),
    path("categories/", TicketCategoryListView.as_view(), name="category-list"),
    path("tickets/", TicketListCreateView.as_view(), name="ticket-list"),
    path("tickets/<int:pk>/", TicketDetailView.as_view(), name="ticket-detail"),
    path("tickets/<int:pk>/comments/", TicketCommentCreateView.as_view(), name="ticket-comments"),
    path("tickets/<int:pk>/agents/", TicketAgentsView.as_view(), name="ticket-agents"),
    path("attachments/<int:pk>/file/", TicketAttachmentFileView.as_view(), name="attachment-file"),
]
