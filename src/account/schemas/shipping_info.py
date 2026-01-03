from ninja import Schema
from typing import Optional


class ShippingInfoRequestSchema(Schema):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class ShippingInfoResponseSchema(Schema):
    id: int
    name: str
    address: str
    phone: str
    is_default: bool
