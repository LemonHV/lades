from django.db import transaction

from account.models import User
from cart.exceptions import CartDoesNotExists
from cart.models import Cart, CartItem
from cart.schemas import CartItemRequestSchema
from product.exceptions import ProductDoesNotExists
from product.models import Product


class CartORM:
    # =========================================
    # 1. ADD PRODUCT TO CART
    # =========================================
    @staticmethod
    @transaction.atomic
    def add_cart_item(user: User, payload: CartItemRequestSchema):
        try:
            product = Product.objects.get(uid=payload.product_uid)
        except Product.DoesNotExist:
            raise ProductDoesNotExists

        cart, _ = Cart.objects.get_or_create(user=user)

        try:
            cart_item = CartItem.objects.get(cart=cart, product=product)
            cart_item.quantity += payload.quantity
            cart_item.price = payload.price
            cart_item.save()
        except CartItem.DoesNotExist:
            cart_item = CartItem.objects.create(
                cart=cart,
                product=product,
                price=payload.price,
                quantity=payload.quantity,
            )

    # =========================================
    # 2. UPDATE PRODUCT QUANTITY IN CART
    # =========================================

    @staticmethod
    def update_quantity_cart_item(cart_item: CartItem, quantity: int):
        cart_item.quantity += quantity
        cart_item.save()

    # =========================================
    # 3. DELETE CART ITEM
    # =========================================

    @staticmethod
    def delete_cart_item(cart_item: CartItem):
        cart_item.delete()

    # =========================================
    # 4. GET ALL CART ITEM
    # =========================================

    @staticmethod
    def get_cart_items(user: User):
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            return []

        return cart.cart_item_fk_cart.all()

    # =========================================
    # 5. GET CART AMOUNT
    # =========================================

    @staticmethod
    def get_cart_total(user: User):
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            return CartDoesNotExists
        return sum(item.total_price for item in cart.cart_item_fk_cart.all())

    # =========================================
    # 6. CLEAR CART
    # =========================================

    @staticmethod
    def clear_cart(user: User):
        try:
            cart = Cart.objects.get(user=user)
            cart.cart_item_fk_cart.all().delete()
        except Cart.DoesNotExist:
            raise CartDoesNotExists
