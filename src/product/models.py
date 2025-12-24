from uuid import uuid4

from django.db import models

from account.models import User


class Brand(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, null=False, blank=False)

    def __str__(self):
        return self.name


class Product(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, null=False, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    type = models.CharField(max_length=100, null=True, blank=True)
    origin_price = models.IntegerField(null=False, blank=False)
    sale_price = models.IntegerField(null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    quantity_in_stock = models.IntegerField(null=False, blank=False)
    brand = models.ForeignKey(
        to=Brand,
        on_delete=models.CASCADE,
        related_name="product_fk_brand",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(
        to=Product,
        on_delete=models.CASCADE,
        related_name="image_fk_product",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )
    url = models.TextField(null=True, blank=True)
    is_main = models.BooleanField(default=False)


class VerifyCode(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    code = models.CharField(max_length=255, null=False, blank=False)
    qr_url = models.TextField(null=True, blank=True)
    max_scan = models.IntegerField(null=False, blank=False, default=3)
    scan_count = models.IntegerField(null=False, blank=False, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(
        to=Product,
        on_delete=models.CASCADE,
        related_name="verifycode_fk_product",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )

    def __str__(self):
        return f"VerifyCode {self.code} for Product {self.product.name}"


class Review(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    product = models.ForeignKey(
        to=Product,
        on_delete=models.CASCADE,
        related_name="review_fk_product",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="review_fk_user",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )
    image_url = models.TextField(null=True, blank=True)
    rating = models.IntegerField(null=False, blank=False)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review {self.user.name} for Product {self.product.name}"

    class Meta:
        unique_together = ("product", "user")
