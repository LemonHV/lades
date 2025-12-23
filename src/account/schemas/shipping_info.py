from ninja import Schema


class ShippingInfoRequestSchema(Schema):
    name: str
    address: str
    phone: str
    is_default: bool


class ShippingInfoResponseSchema(Schema):
    id: int
    name: str
    address: str
    phone: str
    is_default: bool
