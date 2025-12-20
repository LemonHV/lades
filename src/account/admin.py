from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    ordering = ("date_joined",)
    list_display = (
        "email",
        "google_id",
        "is_staff",
        "is_active",
        "date_joined",
    )
    search_fields = ("email",)
    USERNAME_FIELD = "email"
