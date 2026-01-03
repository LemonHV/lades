from router.authenticate import AuthBear
from router.authorize import IsUser, IsAdmin
from router.controller import Controller, api, get, post, put
from router.types import AuthenticatedRequest
from order.schemas import (
    OrderRequestSchema,
    OrderResponseSchema,
)
from order.services import OrderService
from uuid import UUID
from typing import List
from order.utils import OrderStatus


@api(prefix_or_class="orders", tags=["Order"], auth=AuthBear())
class OrderAPI(Controller):
    def __init__(self, service: OrderService):
        self.service = service

    @post("", response=OrderResponseSchema, permissions=[IsUser()])
    def create_order(self, request: AuthenticatedRequest, payload: OrderRequestSchema):
        return self.service.create_order(user=request.user, payload=payload)

    @put("/{uid}")
    def update_order_status(self, uid: UUID, status: OrderStatus):
        self.service.update_order_status(uid=uid, status=status)

    @get("/{uid}", response=OrderResponseSchema)
    def get_order_by_uid(self, uid: UUID):
        return self.service.get_order_by_uid(uid=uid)

    @get("", response=List[OrderResponseSchema])
    def get_user_orders(self, request: AuthenticatedRequest):
        return self.service.get_user_orders(user=request.user)

    @get("/{uid}/print", auth=AuthBear(), permissions=[IsAdmin()])
    def print_order(self, uid: UUID):
        return self.service.print_order(uid=uid)
