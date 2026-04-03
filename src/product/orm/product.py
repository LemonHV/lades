from typing import List, Optional
from uuid import UUID

from django.db import transaction
from django.db.models import Prefetch, Q, QuerySet

from account.models import User
from attachment.models import Attachment
from product.models import Brand, Product, ProductImage, Review, ReviewAttachment
from product.schemas import (
    SearchFilterSortSchema,
)


class ProductORM:
    @staticmethod
    def create_product(**product_info) -> Product:
        return Product.objects.create(**product_info)

    @transaction.atomic
    @staticmethod
    @transaction.atomic
    def bulk_create_product(products: list[Product]) -> list[Product]:
        return Product.objects.bulk_create(products, batch_size=1000)

    @staticmethod
    def get_products(payload: SearchFilterSortSchema) -> QuerySet[Product]:
        query = Q(is_deleted=False)

        if payload.search:
            query &= Q(name__icontains=payload.search) | Q(
                code__icontains=payload.search
            )

        if payload.brand:
            query &= Q(brand__name=payload.brand)

        if payload.min_price is not None:
            query &= Q(sale_price__gte=payload.min_price)

        if payload.max_price is not None:
            query &= Q(sale_price__lte=payload.max_price)

        sort_order = "" if payload.sort == "asc" else "-"
        order_by_field = f"{sort_order}sale_price"

        return (
            Product.objects.filter(query)
            .select_related("brand")
            .prefetch_related(
                Prefetch(
                    "product_images",
                    queryset=ProductImage.objects.select_related("attachment").order_by(
                        "sort_order", "created_at"
                    ),
                    to_attr="images",
                )
            )
            .order_by(order_by_field)
        )

    @staticmethod
    def get_product_by_uid(uid: UUID) -> Optional[Product]:
        return (
            Product.objects.filter(uid=uid, is_deleted=False)
            .select_related("brand")
            .prefetch_related(
                Prefetch(
                    "product_images",
                    queryset=ProductImage.objects.select_related("attachment").order_by(
                        "sort_order", "created_at"
                    ),
                    to_attr="images",
                ),
                Prefetch(
                    "reviews",
                    queryset=Review.objects.select_related("user")
                    .prefetch_related(
                        Prefetch(
                            "review_attachments",
                            queryset=ReviewAttachment.objects.select_related(
                                "attachment"
                            ).order_by("sort_order", "created_at"),
                            to_attr="images",
                        )
                    )
                    .order_by("-created_at"),
                    to_attr="product_reviews",
                ),
            )
            .first()
        )

    @staticmethod
    def get_product_by_code(code: str) -> Optional[Product]:
        return (
            Product.objects.filter(code=code, is_deleted=False)
            .select_related("brand")
            .prefetch_related(
                Prefetch(
                    "product_images",
                    queryset=ProductImage.objects.select_related("attachment").order_by(
                        "sort_order", "created_at"
                    ),
                    to_attr="images",
                ),
                Prefetch(
                    "reviews",
                    queryset=Review.objects.select_related("user")
                    .prefetch_related(
                        Prefetch(
                            "review_attachments",
                            queryset=ReviewAttachment.objects.select_related(
                                "attachment"
                            ).order_by("sort_order", "created_at"),
                            to_attr="images",
                        )
                    )
                    .order_by("-created_at"),
                    to_attr="product_reviews",
                ),
            )
            .first()
        )

    @staticmethod
    def get_products_by_codes(codes: list[str]):
        return (
            Product.objects.filter(code__in=codes)
            .select_related("brand")
            .prefetch_related(
                Prefetch(
                    "product_images",
                    queryset=ProductImage.objects.select_related("attachment").order_by(
                        "sort_order", "created_at"
                    ),
                    to_attr="images",
                )
            )
        )

    @staticmethod
    def update_product(product: Product, **product_info) -> Product:
        filtered_info = {
            field: value for field, value in product_info.items() if value is not None
        }

        for field, value in filtered_info.items():
            setattr(product, field, value)

        if filtered_info:
            product.save(update_fields=[*filtered_info.keys(), "updated_at"])

        return product

    @staticmethod
    def bulk_update_product(products: List[Product], fields: List[str]) -> int:
        return Product.objects.bulk_update(products, fields=fields)

    @staticmethod
    def on_off_product(product: Product) -> Product:
        product.is_deleted = not product.is_deleted
        product.save(update_fields=["is_deleted", "updated_at"])
        return product

    @staticmethod
    def hard_delete_product(product: Product) -> bool:
        product.delete()
        return True

    @staticmethod
    def create_brand(name: str) -> Brand:
        return Brand.objects.create(name=name)

    @staticmethod
    def get_or_create_by_name(name: str) -> tuple[Brand, bool]:
        return Brand.objects.get_or_create(name=name)

    @staticmethod
    def get_brand_by_uid(uid: UUID) -> Optional[Brand]:
        return Brand.objects.filter(uid=uid).first()

    @staticmethod
    def get_brand_by_name(name: str) -> Optional[Brand]:
        return Brand.objects.filter(name=name).first()

    @staticmethod
    def get_brands() -> QuerySet[Brand]:
        return Brand.objects.all()

    @staticmethod
    def update_brand(brand: Brand, name: str) -> Brand:
        brand.name = name
        brand.save(update_fields=["name"])
        return brand

    @staticmethod
    def delete_brand(brand: Brand) -> bool:
        brand.delete()
        return True

    @staticmethod
    def create_product_image(
        product: Product, attachment: Attachment, is_main: bool, sort_order: int
    ):
        return ProductImage.objects.create(
            product=product,
            attachment=attachment,
            is_main=is_main,
            sort_order=sort_order,
        )

    @staticmethod
    def bulk_create_product_images(product_images):
        return ProductImage.objects.bulk_create(product_images)

    @staticmethod
    def get_product_image_by_uid(uid: UUID):
        return ProductImage.objects.filter(uid=uid).first()

    @staticmethod
    def delete_product_image(product_image: ProductImage):
        product_image.delete()
