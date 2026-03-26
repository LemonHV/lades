from typing import List, Optional
from uuid import UUID

from ninja import Field, ModelSchema, Query, Schema
from pydantic import ConfigDict

from account.models import User
from attachment.schemas import AttachmentSchema
from product.models import (
    Brand,
    Product,
    ProductImage,
    Review,
    ReviewAttachment,
    VerifyCode,
    VerifierLocation,
)


### FILTER SCHEMA ###


class SearchFilterSortSchema(Schema):
    search: Optional[str] = Query(None)
    brand: Optional[str] = Query(None)
    min_price: Optional[int] = Query(None)
    max_price: Optional[int] = Query(None)
    sort: str = Query("asc")


### REQUEST SCHEMA ###


class BrandRequestSchema(Schema):
    name: str


class ProductRequestSchema(ModelSchema):
    brand_uid: UUID

    class Meta:
        model = Product
        exclude = ["uid", "brand", "is_deleted", "created_at", "updated_at"]


class ProductUpdateSchema(Schema):
    name: Optional[str] = None
    type: Optional[str] = None
    origin_price: Optional[int] = None
    sale_price: Optional[int] = None
    description: Optional[str] = None
    quantity_in_stock: Optional[int] = None


### RESPONSE SCHEMA ###


class BrandResponseSchema(ModelSchema):
    class Meta:
        model = Brand
        fields = ["uid", "name"]

    model_config = ConfigDict(from_attributes=True)


class ProductImageResponseSchema(ModelSchema):
    attachment: AttachmentSchema

    class Meta:
        model = ProductImage
        exclude = ["created_at"]

    model_config = ConfigDict(from_attributes=True)


class ReviewAttachmentResponseSchema(ModelSchema):
    attachment: AttachmentSchema

    class Meta:
        model = ReviewAttachment
        exclude = ["created_at"]

    model_config = ConfigDict(from_attributes=True)


class UserResponseSchema(ModelSchema):
    class Meta:
        model = User
        fields = ["uid", "name", "email"]

    model_config = ConfigDict(from_attributes=True)


class ReviewResponseSchema(ModelSchema):
    user: UserResponseSchema
    images: List[ReviewAttachmentResponseSchema] = Field(default_factory=list)

    class Meta:
        model = Review
        exclude = ["updated_at"]

    model_config = ConfigDict(from_attributes=True)


class ProductResponseSchema(ModelSchema):
    brand: BrandResponseSchema
    images: List[ProductImageResponseSchema] = Field(default_factory=list)

    class Meta:
        model = Product
        exclude = ["created_at", "updated_at"]

    model_config = ConfigDict(from_attributes=True)


class ProductDetailResponseSchema(ModelSchema):
    brand: BrandResponseSchema
    images: List[ProductImageResponseSchema] = Field(default_factory=list)
    product_reviews: List[ReviewResponseSchema] = Field(default_factory=list)

    class Meta:
        model = Product
        exclude = ["created_at", "updated_at"]

    model_config = ConfigDict(from_attributes=True)


class OnOffResponseSchema(ModelSchema):
    class Meta:
        model = Product
        fields = ["uid", "is_deleted"]

    model_config = ConfigDict(from_attributes=True)


class DeleteProductResponseSchema(Schema):
    success: bool


class DeleteBrandResponseSchema(Schema):
    success: bool


class ProductInfoSchema(Schema):
    name: str
    code: str
    description: str


class PrintQRCodeRequestSchema(Schema):
    quantity: int
    max_scan: Optional[int]


class VerifyCodeResponseSchema(ModelSchema):
    class Meta:
        model = VerifyCode
        fields = ["uid", "code", "max_scan", "scan_count"]

    model_config = ConfigDict(from_attributes=True)


class VerifierLocationResponseSchema(ModelSchema):
    verify_code: VerifyCodeResponseSchema

    class Meta:
        model = VerifierLocation
        fields = "__all__"

    model_config = ConfigDict(from_attributes=True)


class VerifierLocationRequestSchema(Schema):
    verify_code_uid: UUID
    ip_address: Optional[str] = None
    isp: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    region_name: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
