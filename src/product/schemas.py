from typing import List, Optional
from uuid import UUID

from ninja import ModelSchema, Schema

from account.models import User
from product.models import Brand, Product, ProductImage, Review


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


class BrandResponseSchema(ModelSchema):
    class Meta:
        model = Brand
        fields = ["uid", "name"]

    class Config:
        orm_mode = True


class ProductImageResponseSchema(ModelSchema):
    class Meta:
        model = ProductImage
        fields = ["id", "url", "is_main"]

    class Config:
        orm_mode = True


class UserResponseSchema(ModelSchema):
    class Meta:
        model = User
        fields = ["uid", "name", "email"]

    class Config:
        orm_mode = True


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

    class Config:
        orm_mode = True


class ProductResponseSchema(ModelSchema):
    class Meta:
        model = Product
        exclude = ["deleted", "created_at", "updated_at"]

    brand: BrandResponseSchema
    images: Optional[List[ProductImageResponseSchema]]

    class Config:
        orm_mode = True


class ProductUIDResponseSchema(ModelSchema):
    class Meta:
        model = Product
        exclude = ["deleted", "created_at", "updated_at"]

    brand: BrandResponseSchema
    images: Optional[List[ProductImageResponseSchema]]
    reviews: Optional[List[ProductReviewResponseSchema]]

    class Config:
        orm_mode = True


class OnOffResponseSchema(ModelSchema):
    class Meta:
        model = Product
        fields = ["uid", "deleted"]


class DeleteProductResponseSchema(Schema):
    success: bool
