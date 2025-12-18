from django.contrib import admin
from django.utils.html import format_html

from .models import Product, ProductImage, Review


# Inline #
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image_preview", "is_main")
    readonly_fields = ("image_preview",)

    @admin.display(description="Ảnh sản phẩm")
    def image_preview(self, obj):
        if obj.url:
            return format_html(
                '<img src="{}" width="150" height="150" style="margin:2px;" />',
                obj.url,
            )
        return "Chưa có ảnh"


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 1
    fields = ("user", "rating", "comment", "image_preview")
    readonly_fields = ("image_preview",)

    @admin.display(description="Ảnh nhận xét")
    def image_preview(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" width="150" height="150" style="margin:2px;" />',
                obj.image_url,
            )
        return "Chưa có ảnh"


# Admin #
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "brand",
        "origin_price",
        "sale_price",
        "quantity_in_stock",
        "deleted",
        "created_at",
    )

    list_filter = ("brand", "deleted", "created_at")
    search_fields = ("code", "name")
    readonly_fields = ("created_at", "updated_at")

    inlines = [ProductImageInline, ReviewInline]

    ordering = ("-created_at",)
