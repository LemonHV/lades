from typing import List
from uuid import UUID

from account.schemas.account import MessageResponseSchema
from cart.schemas import (
    CartItemRequestSchema,
    CartItemResponseSchema,
    UpdateQuantityCartItemSchema,
)
from cart.services import CartService
from router.authenticate import AuthBear
from router.authorize import IsUser
from router.controller import Controller, api, delete, get, post, put
from router.types import AuthenticatedRequest
from utils.success_message import SuccessMessage


@api(prefix_or_class="carts", tags=["Cart"], auth=AuthBear())
class CartAPI(Controller):
    def __init__(self, service: CartService):
        self.service = service

    @post("", response=MessageResponseSchema, permissions=[IsUser()])
    def add_item_to_cart(
        self, request: AuthenticatedRequest, payload: CartItemRequestSchema
    ):
        self.service.add_item_to_cart(user=request.user, payload=payload)
        return MessageResponseSchema(message=SuccessMessage.CART_ITEM_ADDED)

    @put("/{uid}", response=MessageResponseSchema, permissions=[IsUser()])
    def update_quantity_cart_item(
        self,
        request: AuthenticatedRequest,
        uid: UUID,
        payload: UpdateQuantityCartItemSchema,
    ):
        self.service.update_item_quantity(
            user=request.user,
            cart_item_uid=uid,
            quantity=payload.quantity,
        )
        return MessageResponseSchema(message=SuccessMessage.CART_ITEM_UPDATED)

    @delete("/{uid}", response=MessageResponseSchema, permissions=[IsUser()])
    def delete_cart_item(
        self,
        request: AuthenticatedRequest,
        uid: UUID,
    ):
        self.service.delete_cart_item(
            user=request.user,
            cart_item_uid=uid,
        )
        return MessageResponseSchema(message=SuccessMessage.CART_ITEM_DELETED)

    @get("", response=List[CartItemResponseSchema], permissions=[IsUser()])
    def get_cart_items(self, request: AuthenticatedRequest):
        return self.service.get_cart_items(user=request.user)
