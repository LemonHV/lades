from typing import List, Literal, Optional
from uuid import UUID

from ninja import ModelSchema, Schema
from pydantic import ConfigDict, model_validator

from order.models import Order, OrderItem, Payment
from order.utils import OrderStatus
from product.schemas import ProductResponseSchema


class BuyNowItemSchema(Schema):
    product_uid: UUID
    quantity: int


class OrderRequestSchema(Schema):
    source: Literal["buy_now", "cart"]
    order_items: Optional[list[BuyNowItemSchema]] = None
    cart_item_uids: Optional[list[UUID]] = None

    shipping_info_uid: UUID
    discount_code: Optional[str] = None
    payment_method: Literal["banking", "cod"]
    note: Optional[str] = None

    @model_validator(mode="after")
    def validate_source(self):
        if self.source == "buy_now":
            if not self.order_items:
                raise ValueError("order_items is required when source=buy_now")
            if self.cart_item_uids:
                raise ValueError("cart_item_uids is not allowed when source=buy_now")

        if self.source == "cart":
            if not self.cart_item_uids:
                raise ValueError("cart_item_uids is required when source=cart")
            if self.order_items:
                raise ValueError("order_items is not allowed when source=cart")

        return self


class PaymentResponseSchema(ModelSchema):
    class Meta:
        model = Payment
        fields = ["uid", "status", "method", "amount", "transfer_content", "qr_url"]


class OrderCreateResponseSchema(ModelSchema):
    payment: PaymentResponseSchema

    class Meta:
        model = Order
        fields = ["uid", "code", "status", "total_amount"]


class OrderItemResponseSchema(ModelSchema):
    product: ProductResponseSchema

    class Meta:
        model = OrderItem
        fields = ["uid", "price", "quantity"]

    model_config = ConfigDict(from_attributes=True)


class OrderResponseSchema(ModelSchema):
    order_items: List[OrderItemResponseSchema]

    class Meta:
        model = Order
        exclude = ["user", "discount"]


class UpdateOrderStatusSchema(Schema):
    status: OrderStatus


class DiscountRequestSchema(Schema):
    name: str
    code: str
    type: Literal["percentage", "fixed_amount"]
    value: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    min_order_amount: Optional[int] = None
    max_usage: Optional[int] = None


class DiscountResponseSchema(Schema):
    uid: UUID
    name: str
    code: str
    type: Literal["percentage", "fixed_amount"]
    value: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    min_order_amount: Optional[int] = None
    max_usage: Optional[int] = None


class SePayWebhookSchema(Schema):
    id: int
    gateway: str
    transactionDate: str
    accountNumber: str
    code: Optional[str] = None
    content: str
    transferType: str
    transferAmount: int
    accumulated: int
    subAccount: Optional[str] = None
    referenceCode: str
    description: Optional[str] = ""


class WebhookResponseSchema(Schema):
    success: bool
    message: str


class ConfirmResponseSchema(Schema):
    status: str
    message: str
