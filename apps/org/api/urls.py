from django.urls import path

from .views import DepartmentDetailView, DepartmentListView, OrgChartView

app_name = "org-api"
urlpatterns = [
    path("departments/", DepartmentListView.as_view(), name="department-list"),
    path("departments/<int:pk>/", DepartmentDetailView.as_view(), name="department-detail"),
    path("chart/", OrgChartView.as_view(), name="chart"),
]
