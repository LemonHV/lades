from uuid import uuid4

from django.db import models

from account.models import User
from attachment.models import Attachment


class Brand(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=100, null=True, blank=True)
    origin_price = models.PositiveIntegerField(null=False, blank=False)
    sale_price = models.PositiveIntegerField(null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    quantity_in_stock = models.PositiveIntegerField(null=False, blank=False)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="products")
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["code"]), models.Index(fields=["name"])]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class ProductImage(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    product = models.ForeignKey(
        to=Product, on_delete=models.CASCADE, related_name="product_images"
    )
    attachment = models.ForeignKey(
        Attachment, on_delete=models.CASCADE, related_name="product_image"
    )
    is_main = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def count_by_product(product):
        return ProductImage.objects.filter(product=product).count()

    class Meta:
        ordering = ["sort_order", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "attachment"], name="unique_product_attachment"
            )
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.attachment.uid}"


class VerifyCode(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    code = models.CharField(max_length=255, null=False, blank=False)
    max_scan = models.IntegerField(null=False, blank=False, default=3)
    scan_count = models.IntegerField(null=False, blank=False, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(
        to=Product,
        on_delete=models.CASCADE,
        related_name="verify_code",
        to_field="uid",
        db_index=True,
        null=False,
        blank=False,
    )
    attachment = models.OneToOneField(
        to=Attachment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verify_code",
    )

    def __str__(self):
        return f"VerifyCode {self.code} for Product {self.product.name}"


class VerifierLocation(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    verify_code = models.ForeignKey(
        to=VerifyCode,
        on_delete=models.CASCADE,
        related_name="locations",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    isp = models.CharField(max_length=255, null=True, blank=True)

    country = models.CharField(max_length=100, null=True, blank=True)
    country_code = models.CharField(max_length=10, null=True, blank=True)

    region = models.CharField(max_length=100, null=True, blank=True)
    region_name = models.CharField(max_length=100, null=True, blank=True)

    city = models.CharField(max_length=100, null=True, blank=True)
    zip_code = models.CharField(max_length=20, null=True, blank=True)

    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    timezone = models.CharField(max_length=100, null=True, blank=True)

    scanned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ip_address} - {self.city} ({self.verify_code.code})"

    class Meta:
        ordering = ["-scanned_at"]


class Review(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    product = models.ForeignKey(
        to=Product,
        on_delete=models.CASCADE,
        related_name="reviews",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="reviews",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )
    rating = models.IntegerField(null=False, blank=False)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review {self.user.name} for Product {self.product.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"],
                name="unique_review_per_product_user",
            )
        ]
        unique_together = ("product", "user")


class ReviewAttachment(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    review = models.ForeignKey(
        to=Review,
        on_delete=models.CASCADE,
        related_name="review_attachments",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )
    attachment = models.ForeignKey(
        to=Attachment,
        on_delete=models.CASCADE,
        related_name="review_attachment",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["review", "attachment"],
                name="unique_attachment_per_review",
            )
        ]
        ordering = ["sort_order", "created_at"]

    def __str__(self):
        return f"{self.review.uid} - {self.attachment.uid}"
