from uuid import UUID

from exceptions.product import ProductDoesNotExist
from product.models import Product
from product.orm.product import ProductORM
from product.schemas import ProductRequestSchema, SearchFilterSortSchema


class ProductService:
    def __init__(self):
        self.orm = ProductORM()

    def get_product_file(self):
        return self.orm.get_product_file()

    def create(self, payload: ProductRequestSchema):
        return self.orm.create(payload=payload)

    def create_multiple(self, product_file):
        return self.orm.create_multiple(product_file=product_file)

    def upload_image(self, uid: UUID, image_files: list):
        product = self.get_by_uid(uid=uid)
        return self.orm.upload_image(product=product, image_files=image_files)

    def get_all(self, payload: SearchFilterSortSchema):
        return self.orm.get_all(payload=payload)

    def get_by_uid(self, uid: UUID):
        product = self.orm.get_by_uid(uid=uid)
        if not (product):
            raise ProductDoesNotExist
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
            raise ProductDoesNotExist
