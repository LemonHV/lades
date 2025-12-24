from uuid import UUID

from account.models import User
from cart.exceptions import CartItemDoesNotExists
from cart.models import CartItem
from cart.orm.cart import CartORM
from cart.schemas import CartItemRequestSchema


class CartService:
    def __init__(self):
        self.orm = CartORM()

    def add_cart_item(self, user: User, payload: CartItemRequestSchema):
        self.orm.add_cart_item(user=user, payload=payload)

    def update_quantity_cart_item(self, uid: UUID, quantity: int):
        try:
            cart_item = CartItem.objects.get(uid=uid)
        except CartItem.DoesNotExist:
            raise CartItemDoesNotExists
        self.orm.update_quantity_cart_item(cart_item=cart_item, quantity=quantity)

    def delete_cart_item(self, uid: UUID):
        try:
            cart_item = CartItem.objects.get(uid=uid)
        except CartItem.DoesNotExist:
            raise CartItemDoesNotExists
        self.orm.delete_cart_item(cart_item=cart_item)

    def get_cart_items(self, user: User):
        return self.orm.get_cart_items(user=user)
