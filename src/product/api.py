from product.services.product import ProductService
from product.services.verify_code import VerifyCodeService
from django.template import Context, Template
from uuid import UUID
from typing import List
from ninja import Query
from product.schemas import (
    ProductResponseSchema,
    ProductRequestSchema,
    ProductSchema,
    ProductImageResponseSchema,
    SearchFilterSortSchema,
    ProductUIDResponseSchema,
    OnOffResponseSchema,
    DeleteProductResponseSchema,
)
from router.types import AuthenticatedRequest
from router.authenticate import AuthBear
from router.authorize import IsAdmin
from router.paginate import paginate
from router.controller import Controller, api, delete, get, post, put
from django.http import HttpResponse
from product.utils import VERIFY_QR_TEMPLATE, generate_qrcode_pdf
from router.middleware import get_client_ip


@api(prefix_or_class="products", tags=["Product"], auth=None)
class ProductController(Controller):
    def __init__(self) -> None:
        self.service = ProductService()
        self.verify_code_service = VerifyCodeService()

    @post("", response=ProductResponseSchema, auth=AuthBear(), permissions=[IsAdmin()])
    def create_product(self, payload: ProductRequestSchema):
        return self.service.create_product(payload=payload)

    @get("/product-file", auth=AuthBear(), permissions=[IsAdmin()])
    def get_product_file(self):
        output = self.service.get_product_file()
        response = HttpResponse(
            output,
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = 'attachment; filename="product_list.xlsx"'
        return response

    @post(
        "/multi-product",
        response=List[ProductSchema],
        auth=AuthBear(),
        permissions=[IsAdmin()],
    )
    def create_multiple_products(self, request: AuthenticatedRequest):
        product_file = request.FILES.get("file")
        return self.service.create_multiple_products(product_file=product_file)

    @post(
        "/{uid}/images",
        response=List[ProductImageResponseSchema],
        auth=AuthBear(),
        permissions=[IsAdmin()],
    )
    def upload_images(self, request: AuthenticatedRequest, uid: UUID):
        image_files = request.FILES.getlist("file")
        return self.service.upload_images(uid=uid, image_files=image_files)

    @delete("/images/{uid}", auth=AuthBear(), permissions=[IsAdmin()])
    def delete_image(self, uid: UUID):
        self.service.delete_product_image(uid=uid)

    @get("", response=ProductResponseSchema, paginate=True)
    @paginate
    def get_products(self, payload: SearchFilterSortSchema = Query(...)):
        return self.service.get_products(payload=payload)

    @get("/{uid}", response=ProductUIDResponseSchema)
    def get_product_by_uid(self, uid: UUID):
        return self.service.get_product_by_uid(uid=uid)

    @put(
        "/{uid}",
        response=ProductResponseSchema,
        auth=AuthBear(),
        permissions=[IsAdmin()],
    )
    def update(self, uid: UUID, payload: ProductRequestSchema):
        return self.service.update(uid=uid, payload=payload)

    @put(
        "/{uid}/on-off",
        response=OnOffResponseSchema,
        auth=AuthBear(),
        permissions=[IsAdmin()],
    )
    def on_off_product(self, uid: UUID):
        return self.service.on_off_product(uid=uid)

    @delete(
        "/{uid}/delete",
        response=DeleteProductResponseSchema,
        auth=AuthBear(),
        permissions=[IsAdmin()],
    )
    def delete_product(self, uid: UUID):
        success = self.service.delete_product(uid=uid)
        return DeleteProductResponseSchema(success=success)

    @get("/{uid}/print-qrcode", auth=AuthBear(), permissions=[IsAdmin()])
    def print_qrcode(self, uid: UUID, number_qrcode: int):
        verify_codes = self.verify_code_service.generate_multiple_verify_qr_codes(
            uid=uid, quantity=number_qrcode
        )
        return generate_qrcode_pdf(verify_codes)


@api(prefix_or_class="verifycodes", tags=["Verify Code"], auth=None)
class VerifyCodeController(Controller):
    def __init__(self) -> None:
        self.service = VerifyCodeService()

    @get("/verify-qrcode")
    def verify_qrcode(self, request, code: str):
        client_ip = get_client_ip(request)
        result = self.service.verify_qrcode(code=code, client_ip=client_ip)

        html = Template(VERIFY_QR_TEMPLATE).render(Context(result))
        return HttpResponse(html, content_type="text/html")
