from typing import List
from uuid import UUID

from account.schemas.account import MessageResponseSchema
from account.utils import SuccessMessage
from cart.schemas import (
    CartItemRequestSchema,
    CartItemResponseSchema,
    UpdateQuantityCartITemSchema,
)
from cart.services import CartService
from router.authenticate import AuthBear
from router.authorize import IsUser
from router.controller import Controller, api, delete, get, post, put
from router.types import AuthenticatedRequest


@api(prefix_or_class="carts", tags=["Cart"], auth=AuthBear())
class CartAPI(Controller):
    def __init__(self, service: CartService):
        self.service = service

    @post("", response=MessageResponseSchema, permissions=[IsUser()])
    def add_cart_item(
        self, request: AuthenticatedRequest, payload: CartItemRequestSchema
    ):
        self.service.add_cart_item(user=request.user, payload=payload)
        return MessageResponseSchema(message=SuccessMessage.CART_ITEM_ADDED)

    @put("/{uid}", response=MessageResponseSchema, permissions=[IsUser()])
    def update_quantity_cart_item(
        self, uid: UUID, payload: UpdateQuantityCartITemSchema
    ):
        self.service.update_quantity_cart_item(uid=uid, quantity=payload.quantity)
        return MessageResponseSchema(message=SuccessMessage.CART_ITEM_UPDATED)

    @delete("/{uid}", response=MessageResponseSchema, permissions=[IsUser()])
    def delete_cart_item(self, uid: UUID):
        self.service.delete_cart_item(uid=uid)
        return MessageResponseSchema(message=SuccessMessage.CART_ITEM_DELETED)

    @get("", response=List[CartItemResponseSchema], permissions=[IsUser()])
    def get_cart_items(self, request: AuthenticatedRequest):
        return self.service.get_cart_items(user=request.user)
