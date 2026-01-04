from uuid import UUID
from ninja import Schema, ModelSchema
from cart.models import CartItem
from product.schemas import ProductResponseSchema


class CartItemRequestSchema(Schema):
    product_uid: UUID
    quantity: int


class CartItemResponseSchema(ModelSchema):
    product: ProductResponseSchema

    class Meta:
        model = CartItem
        fields = ["uid", "quantity"]


class UpdateQuantityCartITemSchema(Schema):
    quantity: int
