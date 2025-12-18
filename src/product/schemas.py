from typing import Optional
from uuid import UUID

from ninja import ModelSchema, Schema

from product.models import Product, ProductImage


class ProductRequestSchema(ModelSchema):
    brand_name: str

    class Meta:
        model = Product
        exclude = ["uid", "brand", "deleted", "created_at", "updated_at"]


class SearchFilterSortSchema(Schema):
    search: Optional[str] = None
    brand: Optional[UUID] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    sort: str = "asc"


class ProductResponseSchema(ModelSchema):
    class Meta:
        model = Product
        exclude = [
            "deleted",
        ]


class ProductImageResponseSchema(ModelSchema):
    class Meta:
        model = ProductImage
        fields = ["id", "product", "url", "is_main"]


class OnOffResponseSchema(ModelSchema):
    class Meta:
        model = Product
        fields = ["uid", "deleted"]


class DeleteProductResponseSchema(Schema):
    success: bool
