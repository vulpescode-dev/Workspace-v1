from django.urls import path

from .views import (
    FormDetailView, FormListCreateView, FormQuestionsView, FormResultsCsvView, FormResultsView, FormsMeView, FormSubmitView,
)

app_name = "forms-api"
urlpatterns = [
    path("me/", FormsMeView.as_view(), name="me"),
    path("forms/", FormListCreateView.as_view(), name="form-list"),
    path("forms/<uuid:form_uuid>/", FormDetailView.as_view(), name="form-detail"),
    path("forms/<uuid:form_uuid>/questions/", FormQuestionsView.as_view(), name="form-questions"),
    path("forms/<uuid:form_uuid>/submissions/", FormSubmitView.as_view(), name="form-submit"),
    path("forms/<uuid:form_uuid>/results/", FormResultsView.as_view(), name="form-results"),
    path("forms/<uuid:form_uuid>/results.csv", FormResultsCsvView.as_view(), name="form-results-csv"),
]
