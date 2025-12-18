from typing import List
from uuid import UUID

from product.schemas import (
    DeleteProductResponseSchema,
    OnOffResponseSchema,
    ProductImageResponseSchema,
    ProductRequestSchema,
    ProductResponseSchema,
    SearchFilterSortSchema,
)
from product.services import ProductService
from router.authenticate import AuthBear
from router.authorize import IsAdmin
from router.controller import Controller, api, delete, get, post, put
from router.paginate import paginate
from router.types import AuthenticatedRequest


@api(prefix_or_class="products", tags=["Product"], auth=AuthBear())
class ProductController(Controller):
    def __init__(self, service: ProductService) -> None:
        self.service = service

    @get("/product-file", permissions=[IsAdmin()])
    def get_product_file(self):
        return self.service.get_product_file()

    @post("", response=ProductResponseSchema, permissions=[IsAdmin()])
    def create(self, payload: ProductRequestSchema):
        return self.service.create(payload=payload)

    @post(
        "/multi-product", response=List[ProductResponseSchema], permissions=[IsAdmin()]
    )
    def create_multiple(self, request: AuthenticatedRequest):
        product_file = request.FILES.get("file")
        return self.service.create_multiple(product_file=product_file)

    @post(
        "/{uid}/images",
        response=List[ProductImageResponseSchema],
        permissions=[IsAdmin()],
    )
    def upload_image(self, request: AuthenticatedRequest, uid: UUID):
        image_files = request.FILES.getlist("file")
        return self.service.upload_image(uid=uid, image_files=image_files)

    @get("", response=ProductResponseSchema, paginate=True)
    @paginate
    def get_all(self, payload: SearchFilterSortSchema):
        return self.service.get_all(payload=payload)

    @get("/{uid}", response=ProductResponseSchema)
    def get_by_uid(self, uid: UUID):
        return self.service.get_by_uid(uid=uid)

    @put("/{uid}", response=ProductResponseSchema, permissions=[IsAdmin()])
    def update(self, uid: UUID, payload: ProductRequestSchema):
        return self.service.update(uid=uid, payload=payload)

    @put("/{uid}/on-off", response=OnOffResponseSchema, permissions=[IsAdmin()])
    def on_off(self, uid: UUID):
        return self.service.on_off(uid=uid)

    @delete(
        "/{uid}/delete", response=DeleteProductResponseSchema, permissions=[IsAdmin()]
    )
    def delete_product(self, uid: UUID):
        success = self.service.delete_product(uid=uid)
        return DeleteProductResponseSchema(success=success)
