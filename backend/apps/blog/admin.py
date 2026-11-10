from django.contrib import admin

from .models import Article, ArticleCategory, ArticleComment, ArticleReaction


@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "position", "is_active")
    list_editable = ("position", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "author", "status", "published_at", "deleted_at")
    list_filter = ("status", "category", ("deleted_at", admin.EmptyFieldListFilter))
    search_fields = ("title", "excerpt", "author__username")
    raw_id_fields = ("author",)
    date_hierarchy = "published_at"
    readonly_fields = ("created_at", "updated_at")


@admin.register(ArticleReaction)
class ArticleReactionAdmin(admin.ModelAdmin):
    list_display = ("id", "article", "user", "emoji", "updated_at")
    list_filter = ("emoji",)
    raw_id_fields = ("article", "user")


@admin.register(ArticleComment)
class ArticleCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "article", "parent", "author", "short_body", "created_at", "deleted_at")
    list_filter = (("deleted_at", admin.EmptyFieldListFilter),)
    search_fields = ("body", "author__username")
    raw_id_fields = ("article", "author", "parent")

    @admin.display(description="contenido")
    def short_body(self, obj):
        return obj.body[:60]
