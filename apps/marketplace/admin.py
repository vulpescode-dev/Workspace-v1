from django.contrib import admin

from .models import Listing, ListingCategory, ListingImage


@admin.register(ListingCategory)
class ListingCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "position", "is_active")
    list_editable = ("position", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 0
    fields = ("file", "original_name", "content_type", "size", "width", "height", "position")
    readonly_fields = ("file", "original_name", "content_type", "size", "width", "height")

    def has_add_permission(self, request, obj=None):
        # Las fotos se suben desde la app (validadas); el admin solo consulta o elimina.
        return False


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "seller", "category", "price", "status", "created_at", "deleted_at")
    list_filter = ("status", "category", ("deleted_at", admin.EmptyFieldListFilter))
    inlines = [ListingImageInline]
    search_fields = ("title", "description", "seller__username", "seller__email")
    raw_id_fields = ("seller",)
    date_hierarchy = "created_at"
