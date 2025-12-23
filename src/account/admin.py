from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import AuthenticateToken, ShippingInfo, User


class ShippingInfoInline(admin.TabularInline):
    model = ShippingInfo
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = (
        "email",
        "name",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
    )
    inlines = [ShippingInfoInline]
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
    )

    search_fields = ("email", "name")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("name", "google_id")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )

    USERNAME_FIELD = "email"


@admin.register(ShippingInfo)
class ShippingInfoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "name",
        "phone",
        "address",
        "is_default",
    )

    list_filter = ("is_default",)
    search_fields = ("name", "phone", "address", "user__email")


@admin.register(AuthenticateToken)
class AuthenticateTokenAdmin(admin.ModelAdmin):
    list_display = ("token", "user", "is_available_display", "expires_at")

    @admin.display(boolean=True, description="Available")
    def is_available_display(self, obj):
        return obj.is_available
