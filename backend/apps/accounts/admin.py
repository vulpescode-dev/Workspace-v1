from django.contrib import admin, messages
from django.db.models import Count, Q
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Department, Permission, Role, RolePermission, User, UserRole
from .services.roles import assign_role_to_all_users


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

    def get_inlines(self, request, obj):
        # Al crear no se muestran los roles: los «por defecto» se asignan solos al guardar (señal) y
        # repetirlos aquí chocaría. Se ajustan después, ya en la ficha del usuario.
        return self.inlines if obj else []
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
    list_display = ("name", "is_active", "is_default", "created_at")
    list_filter = ("is_active", "is_default")
    search_fields = ("name", "description")
    ordering = ("name",)
    list_per_page = 25
    inlines = [RolePermissionInline]
    actions = ["assign_to_all_users"]

    @admin.action(description="Asignar a todos los usuarios activos")
    def assign_to_all_users(self, request, queryset):
        for role in queryset:
            added = assign_role_to_all_users(role)
            self.message_user(request, f"«{role}»: asignado a {added} usuario(s) que no lo tenían.", messages.SUCCESS)


class PermissionAppFilter(admin.SimpleListFilter):
    """Filtra por la app del código (lo que va antes del primer punto: «social», «blog»…)."""

    title = "app"
    parameter_name = "app"

    def lookups(self, request, model_admin):
        apps = sorted({code.split(".", 1)[0] for code in Permission.objects.values_list("codename", flat=True)})
        return [(app, app) for app in apps]

    def queryset(self, request, queryset):
        return queryset.filter(codename__startswith=f"{self.value()}.") if self.value() else queryset


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Solo lectura: los permisos salen del catálogo ``apps/accounts/data/permissions.json``
    (``manage.py load_permissions``). Aquí se consultan; se asignan a roles desde cada rol."""

    list_display = ("codename", "description")
    list_filter = (PermissionAppFilter,)
    search_fields = ("codename", "description")
    ordering = ("codename",)
    list_per_page = 100

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "assigned_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email", "role__name")
    list_select_related = ("user", "role")
    ordering = ("-assigned_at",)
    list_per_page = 25
    date_hierarchy = "assigned_at"


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
