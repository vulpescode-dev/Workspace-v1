from django.contrib import admin

from .models import CommentReaction, Follow, Post, PostAttachment, PostComment, PostReaction


class PostAttachmentInline(admin.TabularInline):
    model = PostAttachment
    extra = 0
    fields = ("kind", "file", "original_name", "content_type", "size", "width", "height", "position")
    readonly_fields = ("kind", "file", "original_name", "content_type", "size", "width", "height")
    can_delete = True

    def has_add_permission(self, request, obj=None):
        # Los adjuntos se suben desde la app (validados); el admin solo consulta o elimina.
        return False


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "short_body", "audience", "created_at", "edited_at", "deleted_at")
    list_filter = ("audience", ("deleted_at", admin.EmptyFieldListFilter))
    inlines = [PostAttachmentInline]
    search_fields = ("body", "author__username", "author__email")
    raw_id_fields = ("author",)
    date_hierarchy = "created_at"

    @admin.display(description="contenido")
    def short_body(self, obj):
        return obj.body[:60]


@admin.register(PostReaction)
class PostReactionAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "emoji", "updated_at")
    list_filter = ("emoji",)
    raw_id_fields = ("post", "user")


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "parent", "author", "short_body", "created_at", "edited_at", "deleted_at")
    list_filter = (("deleted_at", admin.EmptyFieldListFilter),)
    search_fields = ("body", "author__username")
    raw_id_fields = ("post", "author", "parent")

    @admin.display(description="contenido")
    def short_body(self, obj):
        return obj.body[:60]


@admin.register(CommentReaction)
class CommentReactionAdmin(admin.ModelAdmin):
    list_display = ("id", "comment", "user", "emoji", "updated_at")
    list_filter = ("emoji",)
    raw_id_fields = ("comment", "user")


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("id", "follower", "following", "created_at")
    raw_id_fields = ("follower", "following")
