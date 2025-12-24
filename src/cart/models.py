from uuid import uuid4

from django.db import models

from account.models import User
from product.models import Product


class Cart(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="cart_fk_user",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )


class CartItem(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    cart = models.ForeignKey(
        to=Cart,
        on_delete=models.CASCADE,
        related_name="cart_item_fk_cart",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )
    product = models.ForeignKey(
        to=Product,
        on_delete=models.CASCADE,
        related_name="cart_item_fk_product",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()

    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.name} {self.quantity}"
