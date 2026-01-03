from ninja import Schema
from typing import List, Literal, Optional
from uuid import UUID


class OrderItemRequestSchema(Schema):
    product_uid: UUID
    quantity: int


class OrderRequestSchema(Schema):
    source: Literal["buy_now", "cart"]
    shipping_info_id: int
    note: Optional[str] = None
    discount_code: Optional[str] = None
    order_items: List[OrderItemRequestSchema]


class OrderResponseSchema(Schema):
    uid: UUID
    code: str
    status: str
    total_amount: int


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
