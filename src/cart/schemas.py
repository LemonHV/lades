from uuid import UUID

from ninja import ModelSchema, Schema

from cart.models import CartItem
from product.schemas import ProductResponseSchema


class CartItemRequestSchema(Schema):
    product_uid: UUID
    quantity: int

class UpdateQuantityCartItemSchema(Schema):
    quantity: int

class CartItemResponseSchema(ModelSchema):
    product: ProductResponseSchema

    class Meta:
        model = CartItem
        fields = ["uid", "quantity"]
