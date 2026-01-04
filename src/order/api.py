from router.authenticate import AuthBear
from router.authorize import IsUser, IsAdmin
from router.controller import Controller, api, get, post, put
from router.types import AuthenticatedRequest
from order.schemas import (
    OrderRequestSchema,
    OrderResponseSchema,
    OrderCreateResponseSchema,
    DiscountRequestSchema,
    DiscountResponseSchema,
)
from account.schemas.account import MessageResponseSchema
from account.utils import SuccessMessage
from order.services import OrderService
from uuid import UUID
from typing import List
from order.utils import OrderStatus


@api(prefix_or_class="orders", tags=["Order"], auth=AuthBear())
class OrderAPI(Controller):
    def __init__(self, service: OrderService):
        self.service = service

    @post("", response=OrderCreateResponseSchema, permissions=[IsUser()])
    def create_order(self, request: AuthenticatedRequest, payload: OrderRequestSchema):
        return self.service.create_order(user=request.user, payload=payload)

    @put("/{uid}", response=MessageResponseSchema)
    def update_order_status(self, uid: UUID, status: OrderStatus):
        self.service.update_order_status(uid=uid, status=status)
        return MessageResponseSchema(message=SuccessMessage.UPDATE_ORDER_STATUS_SUCCESS)

    @get("", response=List[OrderResponseSchema])
    def get_all_orders(self, request: AuthenticatedRequest):
        if request.user.is_staff:
            return self.service.get_admin_orders()
        else:
            return self.service.get_user_orders(user=request.user)

    @get("/{uid}", response=OrderResponseSchema)
    def get_order_by_uid(self, uid: UUID):
        return self.service.get_order_by_uid(uid=uid)

    @get("/{uid}/print", auth=AuthBear(), permissions=[IsAdmin()])
    def print_order(self, uid: UUID):
        return self.service.print_order(uid=uid)


@api(prefix_or_class="discounts", tags=["Discount"], auth=AuthBear())
class DiscountAPI(Controller):
    def __init__(self, service: OrderService):
        self.service = service

    @post("", permissions=[IsAdmin()], response=DiscountResponseSchema)
    def create_discount(self, payload: DiscountRequestSchema):
        return self.service.create_discount(payload=payload)

    @get("/{uid}", response=DiscountResponseSchema)
    def get_discount_by_uid(self, uid: UUID):
        return self.service.get_discount_by_uid(uid=uid)

    @get("", response=List[DiscountResponseSchema])
    def get_discounts(self):
        return self.service.get_discounts()

    @put("/{uid}", permissions=[IsAdmin()], response=DiscountResponseSchema)
    def update_discount(self, uid: UUID, payload: DiscountRequestSchema):
        return self.service.update_discount(uid=uid, payload=payload)
