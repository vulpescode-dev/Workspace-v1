from django.contrib import admin

from .models import Document, DocumentCategory, DocumentVersion


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "position", "is_active")
    list_editable = ("position", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")


class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    fields = ("number", "original_name", "content_type", "size", "notes", "uploaded_by", "created_at")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        # Las versiones se suben desde la app (validadas); el admin solo consulta el historial.
        return False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "visibility", "owner", "current_version", "updated_at", "deleted_at")
    list_filter = ("visibility", "category", ("deleted_at", admin.EmptyFieldListFilter))
    search_fields = ("title", "description", "owner__username", "owner__email")
    raw_id_fields = ("owner",)
    autocomplete_fields = ("departments",)
    filter_horizontal = ("shared_with",)
    list_select_related = ("category", "owner", "current_version")
    readonly_fields = ("current_version", "created_at", "updated_at")
    inlines = [DocumentVersionInline]
    date_hierarchy = "updated_at"
    list_per_page = 50
