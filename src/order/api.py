from typing import List
from uuid import UUID
from ninja import Query

from account.schemas.account import MessageResponseSchema
from order.schemas import (
    ConfirmResponseSchema,
    DiscountRequestSchema,
    DiscountResponseSchema,
    OrderCreateResponseSchema,
    OrderRequestSchema,
    OrderResponseSchema,
    SePayWebhookSchema,
    UpdateOrderStatusSchema,
    WebhookResponseSchema,
    SearchFilterSortSchema,
)
from order.services import OrderService, PaymentService
from router.authenticate import AuthBear
from router.authorize import IsAdmin, IsUser
from router.controller import Controller, api, get, post, put
from router.paginate import paginate
from router.types import AuthenticatedRequest
from utils.success_message import SuccessMessage


@api(prefix_or_class="orders", tags=["Order"], auth=AuthBear())
class OrderAPI(Controller):
    def __init__(self, service: OrderService):
        self.service = service

    @post("", response=OrderCreateResponseSchema, permissions=[IsUser()])
    def create_order(self, request: AuthenticatedRequest, payload: OrderRequestSchema):
        return self.service.create_order(user=request.user, payload=payload)

    @put("/{uid}", response=MessageResponseSchema)
    def update_order_status(self, uid: UUID, payload: UpdateOrderStatusSchema):
        self.service.update_order_status(uid=uid, payload=payload)
        return MessageResponseSchema(message=SuccessMessage.UPDATE_ORDER_STATUS_SUCCESS)

    @get("", response=OrderResponseSchema, paginate=True)
    @paginate
    def get_all_orders(
        self,
        request: AuthenticatedRequest,
        payload: SearchFilterSortSchema = Query(...),
    ):
        if request.user.is_staff:
            return self.service.get_admin_orders(payload=payload)
        else:
            return self.service.get_user_orders(user=request.user, payload=payload)

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

    @get("/apply/{code}", response=DiscountResponseSchema)
    def get_discount_by_code(self, code: str):
        return self.service.get_discount_by_code(code=code)


@api(prefix_or_class="payments", tags=["Payment"], auth=None)
class PaymentAPI(Controller):
    def __init__(self):
        self.service = PaymentService()

    @post("/webhook", auth=None, response=WebhookResponseSchema)
    def sepay_webhook(self, request, payload: SePayWebhookSchema):
        return self.service.handle_sepay_webhook(payload)

    @get(
        "/{uid}/check",
        auth=AuthBear(),
        permissions=[IsUser()],
        response=ConfirmResponseSchema,
    )
    def confirm_payment_success(self, request: AuthenticatedRequest, uid: UUID):
        return self.service.confirm_payment_success(uid=uid, user=request.user)
