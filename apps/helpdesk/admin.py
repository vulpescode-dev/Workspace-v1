from django.contrib import admin

from .models import Ticket, TicketAttachment, TicketCategory, TicketComment, TicketEvent


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "kind", "position", "is_active")
    list_editable = ("position", "is_active")
    list_filter = ("department", "kind", "is_active")
    search_fields = ("name", "description", "department__name")
    autocomplete_fields = ("department",)
    list_select_related = ("department",)


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0
    fields = ("original_name", "content_type", "size", "comment", "uploaded_by", "created_at")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        # Los archivos se suben desde la app (validados); el admin solo consulta o elimina.
        return False


class TicketCommentInline(admin.StackedInline):
    model = TicketComment
    extra = 0
    fields = ("author", "body", "is_internal", "created_at")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class TicketEventInline(admin.TabularInline):
    model = TicketEvent
    extra = 0
    fields = ("created_at", "actor", "kind", "old_value", "new_value")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("folio", "title", "department", "category", "status", "priority", "requester", "assignee", "created_at")
    list_filter = ("status", "priority", "department", "category")
    search_fields = ("title", "description", "requester__username", "requester__email", "assignee__username")
    raw_id_fields = ("requester", "assignee")
    list_select_related = ("department", "category", "requester", "assignee")
    readonly_fields = ("created_at", "updated_at", "first_response_at", "resolved_at", "closed_at")
    inlines = [TicketCommentInline, TicketAttachmentInline, TicketEventInline]
    date_hierarchy = "created_at"
    list_per_page = 50
