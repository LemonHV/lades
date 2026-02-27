from typing import List, Optional
from uuid import UUID
from pydantic import ConfigDict
from ninja import ModelSchema, Query, Schema

from account.models import User
from product.models import Brand, Product, ProductImage, Review


class ProductRequestSchema(ModelSchema):
    brand_name: str

    class Meta:
        model = Product
        exclude = ["uid", "brand", "deleted", "created_at", "updated_at"]


class SearchFilterSortSchema(Schema):
    search: Optional[str] = Query(None)
    brand: Optional[UUID] = Query(None)
    min_price: Optional[int] = Query(None)
    max_price: Optional[int] = Query(None)
    sort: str = Query("asc")


class BrandResponseSchema(ModelSchema):
    class Meta:
        model = Brand
        fields = ["uid", "name"]

    model_config = ConfigDict(from_attributes=True)


class ProductImageResponseSchema(ModelSchema):
    class Meta:
        model = ProductImage
        fields = ["id", "url", "is_main"]

    model_config = ConfigDict(from_attributes=True)


class UserResponseSchema(ModelSchema):
    class Meta:
        model = User
        fields = ["uid", "name", "email"]

    model_config = ConfigDict(from_attributes=True)


class ProductReviewResponseSchema(ModelSchema):
    user: UserResponseSchema

    class Meta:
        model = Review
        fields = [
            "uid",
            "rating",
            "comment",
            "image_url",
            "created_at",
            "updated_at",
            "user",
        ]

    model_config = ConfigDict(from_attributes=True)


class ProductSchema(ModelSchema):
    class Meta:
        model = Product
        exclude = ["deleted", "created_at", "updated_at"]


class ProductResponseSchema(ModelSchema):
    class Meta:
        model = Product
        exclude = ["created_at", "updated_at"]

    brand: BrandResponseSchema
    images: Optional[List[ProductImageResponseSchema]] = []

    model_config = ConfigDict(from_attributes=True)


class ProductUIDResponseSchema(ModelSchema):
    class Meta:
        model = Product
        exclude = ["deleted", "created_at", "updated_at"]

    brand: BrandResponseSchema
    images: Optional[List[ProductImageResponseSchema]]
    reviews: Optional[List[ProductReviewResponseSchema]]

    model_config = ConfigDict(from_attributes=True)


class OnOffResponseSchema(ModelSchema):
    class Meta:
        model = Product
        fields = ["uid", "deleted"]


class DeleteProductResponseSchema(Schema):
    success: bool


class VerifyCodeSchema(Schema):
    uid: UUID
    code: str
    qr_url: str
    max_scan: int
    scan_count: int
