from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Permission, Role, RolePermission, User, UserRole


class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 0
    autocomplete_fields = ["role"]


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "job_title", "department", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "is_superuser", "department", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name", "job_title")
    autocomplete_fields = ("department", "manager")
    list_select_related = ("department",)
    ordering = ("username",)
    list_per_page = 25
    date_hierarchy = "date_joined"
    inlines = [UserRoleInline]
    # La foto se sube desde la app (validada y convertida a WebP); aquí solo se consulta.
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Perfil Workspace", {"fields": ("job_title", "department", "manager", "birth_date", "gender", "marital_status", "bio", "avatar", "profile_updated_at")}),
    )
    readonly_fields = ("avatar", "profile_updated_at")
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Perfil Workspace", {"fields": ("email", "job_title")}),
    )


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0
    autocomplete_fields = ["permission"]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    ordering = ("name",)
    list_per_page = 25
    inlines = [RolePermissionInline]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("codename", "description")
    search_fields = ("codename", "description")
    ordering = ("codename",)
    list_per_page = 50


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "assigned_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email", "role__name")
    list_select_related = ("user", "role")
    ordering = ("-assigned_at",)
    list_per_page = 25
    date_hierarchy = "assigned_at"
