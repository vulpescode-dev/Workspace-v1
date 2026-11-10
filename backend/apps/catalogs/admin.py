from django.contrib import admin
from django.utils.html import format_html

from .models import Emoji


@admin.register(Emoji)
class EmojiAdmin(admin.ModelAdmin):
    list_display = ("preview", "label", "code", "codepoint", "position", "is_active")
    list_display_links = ("preview", "label")
    list_editable = ("position", "is_active")
    list_filter = ("is_active",)
    search_fields = ("label", "code", "codepoint")
    readonly_fields = ("preview",)

    @admin.display(description="emoji")
    def preview(self, obj):
        return format_html('<img src="{}" alt="{}" width="24" height="24">', obj.svg_url, obj.char)

    def has_delete_permission(self, request, obj=None):
        # Se desactiva en lugar de borrar: las reacciones lo protegen (PROTECT).
        return False
