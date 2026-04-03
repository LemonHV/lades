from django.db import IntegrityError, transaction
from django.db.models import Prefetch, QuerySet

from account.models import User
from cart.exceptions import CartItemDoesNotExists, CartItemQuantityInvalid
from cart.models import Cart, CartItem
from cart.schemas import CartItemRequestSchema
from product.models import ProductImage
from product.orm.product import ProductORM


class CartORM:
    @staticmethod
    def get_or_create_cart(user: User) -> Cart:
        try:
            with transaction.atomic():
                cart, _ = Cart.objects.get_or_create(user=user)
                return cart
        except IntegrityError:
            return Cart.objects.get(user=user)

    @staticmethod
    def add_item_to_cart(cart: Cart, payload: CartItemRequestSchema) -> CartItem:
        if payload.quantity <= 0:
            raise CartItemQuantityInvalid
        product = ProductORM.get_product_by_uid(uid=payload.product_uid)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                "price": product.sale_price,
                "quantity": payload.quantity,
            },
        )

        if not created:
            cart_item.quantity += payload.quantity
            cart_item.price = product.sale_price
            cart_item.save(update_fields=["quantity", "price"])

        return cart_item

    @staticmethod
    def update_item_quantity(
        cart: Cart, cart_item_uid, quantity: int
    ) -> CartItem | None:
        cart_item = CartItem.objects.filter(
            uid=cart_item_uid,
            cart=cart,
        ).first()
        if not cart_item:
            raise CartItemDoesNotExists
        if quantity <= 0:
            cart_item.delete()
            return None
        cart_item.quantity = quantity
        cart_item.save(update_fields=["quantity"])
        return cart_item

    @staticmethod
    def delete_cart_item(cart: Cart, cart_item_uid) -> bool:
        deleted_count, _ = CartItem.objects.filter(
            uid=cart_item_uid,
            cart=cart,
        ).delete()
        return deleted_count > 0

    @staticmethod
    def clear_cart(cart: Cart) -> None:
        CartItem.objects.filter(cart=cart).delete()

    @staticmethod
    def get_cart_items(cart: Cart) -> QuerySet[CartItem]:
        return (
            CartItem.objects.filter(cart=cart)
            .select_related("product", "product__brand")
            .prefetch_related(
                Prefetch(
                    "product__images",
                    queryset=ProductImage.objects.select_related("attachment"),
                    to_attr="images",
                )
            )
        )
