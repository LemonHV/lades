from uuid import uuid4

from django.db import models
from django.db.models import F, IntegerField, Sum
from django.db.models.functions import Coalesce

from account.models import User
from product.models import Product


class Cart(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="cart",
        to_field="uid",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_amount(self) -> int:
        return self.items.aggregate(
            total=Coalesce(
                Sum(
                    F("price") * F("quantity"),
                    output_field=IntegerField(),
                ),
                0,
            )
        )["total"]

    @property
    def total_items(self) -> int:
        return self.items.aggregate(
            total=Coalesce(Sum("quantity"), 0)
        )["total"]

    def clear(self) -> None:
        self.items.all().delete()


class CartItem(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        to_field="uid",
        db_index=True,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items",
        to_field="uid",
        db_index=True,
    )
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="unique_product_per_cart",
            ),
        ]
        indexes = [
            models.Index(fields=["cart"]),
            models.Index(fields=["product"]),
            models.Index(fields=["cart", "product"]),
        ]

    @property
    def total_price(self) -> int:
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.name} {self.quantity}"
