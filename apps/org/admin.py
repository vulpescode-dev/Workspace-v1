from django.contrib import admin
from django.db.models import Count, Q

from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "head", "members_count", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "description")
    autocomplete_fields = ("parent", "head")
    list_select_related = ("parent", "head")
    ordering = ("name",)
    list_per_page = 50

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _members=Count("members", filter=Q(members__is_active=True)),
        )

    @admin.display(description="personas", ordering="_members")
    def members_count(self, department):
        return department._members
