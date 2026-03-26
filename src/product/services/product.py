from typing import Any
from uuid import UUID
from io import BytesIO
from product.orm.product import ProductORM
from product.schemas import ProductRequestSchema, SearchFilterSortSchema
from product.exceptions import (
    BrandDoesNotExists,
    ProductFileRequired,
    ProductDoesNotExists,
    ProductImageDoesNotExists,
)
from product.models import Product, Brand, ProductImage
from account.models import User
from product.utils import build_product_workbook, load_product_information
from attachment.services import AttachmentService
from attachment.models import AttachmentType


class ProductService:
    def __init__(self):
        self.orm = ProductORM()
        self.attachment_service = AttachmentService()

    def create_product(self, payload: ProductRequestSchema):
        product_info = payload.dict()
        brand_uid = product_info.pop("brand_uid")
        brand = self.orm.get_brand_by_uid(uid=brand_uid)
        if not brand:
            raise BrandDoesNotExists
        return self.orm.create_product(**product_info, brand=brand)

    def get_product_file(self):
        return build_product_workbook()

    def create_multiple_products(self, product_file):
        if not product_file:
            raise ProductFileRequired

        products_data = load_product_information(product_file=product_file)
        brand_cache: dict[str, Brand] = {}
        product_map: dict[str, Product] = {}
        image_map: dict[str, Any] = {}

        for product_data in products_data:
            brand_name = product_data.pop("brand_name", None)
            image = product_data.pop("image", None)

            brand = None
            if brand_name:
                if brand_name not in brand_cache:
                    brand_cache[brand_name], _ = self.orm.get_or_create_by_name(
                        name=brand_name
                    )
                brand = brand_cache[brand_name]

            product_code = product_data["code"]
            product_map[product_code] = Product(**product_data, brand=brand)

            if image:
                image_map[product_code] = image

        codes = list(product_map.keys())
        existing_products = self.orm.get_products_by_codes(codes=codes)
        existing_code_set = {product.code for product in existing_products}

        new_products = [
            product
            for code, product in product_map.items()
            if code not in existing_code_set
        ]
        if new_products:
            self.orm.bulk_create_product(new_products)

        for existing_product in existing_products:
            new_product_data = product_map[existing_product.code]
            existing_product.name = new_product_data.name
            existing_product.origin_price = new_product_data.origin_price
            existing_product.sale_price = new_product_data.sale_price
            existing_product.brand = new_product_data.brand
            existing_product.type = new_product_data.type
            existing_product.description = new_product_data.description
            existing_product.quantity_in_stock = new_product_data.quantity_in_stock

        if existing_products:
            self.orm.bulk_update_product(
                list(existing_products),
                fields=[
                    "name",
                    "origin_price",
                    "sale_price",
                    "brand",
                    "type",
                    "description",
                    "quantity_in_stock",
                ],
            )

        all_products = self.orm.get_products_by_codes(codes=codes)

        for product in all_products:
            image_object = image_map.get(product.code)
            if not image_object:
                continue

            buffer = BytesIO(image_object._data())
            buffer.seek(0)

            attachment = self.attachment_service.upload_attachment(
                file=buffer,
                folder="product_images",
                public_id=f"product_{product.uid}_0",
                type=AttachmentType.PRODUCT,
            )
            self.orm.create_product_image(
                product=product, attachment=attachment, is_main=True, sort_order=0
            )

        return list(all_products)

    def upload_images(self, uid: UUID, image_files: list):
        product = self.orm.get_product_by_uid(uid=uid)
        if not product:
            raise ProductDoesNotExists

        product_images = []

        current_count = ProductImage.count_by_product(product)

        for idx, image_file in enumerate(image_files, start=current_count):
            attachment = self.attachment_service.upload_attachment(
                file=image_file.file,
                folder="product_images",
                public_id=f"product_{product.uid}_{idx}",
                type=AttachmentType.PRODUCT,
            )
            product_image = self.orm.create_product_image(
                product=product, attachment=attachment, is_main=False, sort_order=idx
            )

            product_images.append(product_image)

        return product_images

    def delete_product_image(self, uid: UUID):
        product_image = self.orm.get_product_image_by_uid(uid=uid)
        if not product_image:
            raise ProductImageDoesNotExists
        attachment_uid = (
            product_image.attachment.uid if product_image.attachment else None
        )
        self.orm.delete_product_image(product_image=product_image)
        if attachment_uid:
            self.attachment_service.delete_attachment(attachment_uid)

    def get_products(self, payload: SearchFilterSortSchema, user: User):
        return self.orm.get_products(payload=payload, user=user)

    def get_product_by_uid(self, uid: UUID):
        product = self.orm.get_product_by_uid(uid=uid)
        if not product:
            raise ProductDoesNotExists
        return product

    def update_product(self, uid: UUID, payload: ProductRequestSchema):
        product = self.orm.get_product_by_uid(uid=uid)
        if not product:
            raise ProductDoesNotExists
        product_info = payload.dict()
        return self.orm.update_product(product=product, **product_info)

    def on_off_product(self, uid: UUID):
        product = self.orm.get_product_by_uid(uid=uid)
        if not product:
            raise ProductDoesNotExists
        return self.orm.on_off_product(product=product)

    def delete_product(self, uid: UUID):
        product = self.orm.get_product_by_uid(uid=uid)
        if not product:
            raise ProductDoesNotExists
        return self.orm.hard_delete_product(product=product)

    def create_brand(self, name: str):
        return self.orm.create_brand(name=name)

    def get_brands(self):
        return self.orm.get_brands()

    def get_brand_by_uid(self, uid: UUID):
        return self.orm.get_brand_by_uid(uid=uid)

    def delete_brand(self, uid: UUID):
        brand = self.orm.get_brand_by_uid(uid=uid)
        return self.orm.delete_brand(brand=brand)
