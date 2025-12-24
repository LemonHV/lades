from uuid import UUID

from product.exceptions import ProductDoesNotExists, ProductFileRequired
from product.models import Product
from product.orm.product import ProductORM
from product.schemas import ProductRequestSchema, SearchFilterSortSchema


class ProductService:
    def __init__(self):
        self.orm = ProductORM()

    def create(self, payload: ProductRequestSchema):
        return self.orm.create(payload=payload)

    def get_product_file(self):
        return self.orm.get_product_file()

    def create_multiple(self, product_file):
        if not product_file:
            raise ProductFileRequired
        return self.orm.create_multiple(product_file=product_file)

    def upload_image(self, uid: UUID, image_files: list):
        product = self.get_by_uid(uid=uid)
        return self.orm.upload_image(product=product, image_files=image_files)

    def get_all(self, payload: SearchFilterSortSchema):
        return self.orm.get_all(payload=payload)

    def get_by_uid(self, uid: UUID):
        product = self.orm.get_by_uid(uid=uid)
        if not product:
            raise ProductDoesNotExists
        return product

    def update(self, uid: UUID, payload: ProductRequestSchema):
        return self.orm.update(
            product=self.get_by_uid(uid=uid),
            payload=payload,
        )

    def on_off(self, uid: UUID):
        return self.orm.on_off(product=Product.objects.get(uid=uid))

    def delete_product(self, uid: UUID):
        try:
            return self.orm.delete_product(product=Product.objects.get(uid=uid))
        except Product.DoesNotExist:
            raise ProductDoesNotExists

    def generate_product_verify_code(self, uid: UUID, number_qrcode: int):
        try:
            product = Product.objects.get(uid=uid)
        except Product.DoesNotExist:
            raise ProductDoesNotExists
        return self.orm.generate_product_verify_code(
            product=product, number_qrcode=number_qrcode
        )

    def verify_qrcode(self, code: str):
        return self.orm.verify_qrcode(code=code)
