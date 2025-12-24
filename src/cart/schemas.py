from uuid import UUID

from ninja import Schema


class CartItemRequestSchema(Schema):
    product_uid: UUID
    price: int
    quantity: int


class CartItemResponseSchema(Schema):
    uid: UUID
    price: int
    quantity: int


class UpdateQuantityCartITemSchema(Schema):
    quantity: int
