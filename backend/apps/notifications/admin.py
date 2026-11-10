from django.contrib import admin

from .models import Notification, PushSubscription


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient", "title", "color", "created_at", "read_at")
    list_filter = ("color", ("read_at", admin.EmptyFieldListFilter))
    search_fields = ("title", "body", "recipient__username", "recipient__email")
    raw_id_fields = ("recipient",)


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "short_user_agent", "created_at", "last_used_at")
    search_fields = ("user__username", "user__email", "user_agent")
    raw_id_fields = ("user",)
    readonly_fields = ("endpoint", "p256dh", "auth", "user_agent", "created_at", "last_used_at")

    @admin.display(description="navegador / dispositivo")
    def short_user_agent(self, obj):
        return obj.user_agent[:60]
