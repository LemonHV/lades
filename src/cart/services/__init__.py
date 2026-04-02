from uuid import UUID

from account.models import User
from cart.exceptions import CartItemDoesNotExists
from cart.models import CartItem
from cart.orm.cart import CartORM
from cart.schemas import CartItemRequestSchema


class CartService:
    def __init__(self):
        self.orm = CartORM()
        
    def add_item_to_cart(self, user: User, payload: CartItemRequestSchema):
        cart = self.orm.get_or_create_cart(user=user)
        return self.orm.add_item_to_cart(cart=cart, payload=payload)    
    
    def update_item_quantity(self, user: User, cart_item_uid: UUID, quantity: int):
        cart = self.orm.get_or_create_cart(user=user)
        return self.orm.update_item_quantity(cart=cart, cart_item_uid=cart_item_uid, quantity=quantity)

    def delete_cart_item(self, user: User, cart_item_uid: UUID):
        cart = self.orm.get_or_create_cart(user=user)
        return self.orm.delete_cart_item(cart=cart, cart_item_uid=cart_item_uid)
    
    def clear_cart(self, user: User):
        cart = self.orm.get_or_create_cart(user=user)
        self.orm.clear_cart(cart=cart)

    def get_cart_items(self, user: User):
        cart = self.orm.get_or_create_cart(user=user)
        return self.orm.get_cart_items(cart=cart)
