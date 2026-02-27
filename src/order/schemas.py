from ninja import Schema, ModelSchema
from typing import Literal, Optional, List
from uuid import UUID
from pydantic import model_validator, ConfigDict
from order.models import Order, OrderItem
from product.schemas import ProductResponseSchema
from order.utils import OrderStatus

class BuyNowItemSchema(Schema):
    product_uid: UUID
    quantity: int


class OrderRequestSchema(Schema):
    source: Literal["buy_now", "cart"]
    order_items: Optional[list[BuyNowItemSchema]] = None
    cart_item_uids: Optional[list[UUID]] = None

    shipping_info_id: int
    discount_code: Optional[str] = None
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


class OrderCreateResponseSchema(Schema):
    uid: UUID
    code: str
    status: str
    total_amount: int


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
        exclude = ["user", "payment", "discount"]


class UpdateOrderStatusSchema(Schema):
    status: OrderStatus


class SepayPaymentResponseSchema(Schema):
    order_code: str
    amount: int
    qr_url: str
    bank_name: str
    account_no: str
    account_name: str
    transfer_content: str


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
