from uuid import UUID
from io import BytesIO
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import HttpResponse

from product.models import Brand, Product, ProductImage, Review, VerifyCode
from product.schemas import ProductRequestSchema, SearchFilterSortSchema
from product.utils import (
    build_product_workbook,
    generate_qrcode,
    load_product_infomation,
    upload_file,
)


class ProductORM:
    # =========================================
    # 1. CREATE PRODUCT
    # =========================================

    @staticmethod
    @transaction.atomic
    def create(payload: ProductRequestSchema) -> Product:
        product_brand, _ = Brand.objects.get_or_create(name=payload.brand_name)
        product = Product(**payload.dict(exclude={"brand", "brand_name"}))
        product.brand = product_brand
        product.save()
        return product

    # =========================================
    # 2. GET PRODUCT FILE
    # =========================================
    @staticmethod
    def get_product_file() -> HttpResponse:
        output = build_product_workbook()

        response = HttpResponse(
            output,
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = 'attachment; filename="product_list.xlsx"'
        return response

    # =========================================
    # 3. MULTIPLE CREATE PRODUCT
    # =========================================

    @staticmethod
    @transaction.atomic
    def create_multiple(product_file):
        # 1. Load dữ liệu từ file (Excel)
        products_data = load_product_infomation(product_file=product_file)

        # 2. Cache Brand để không query DB nhiều lần
        brand_cache: dict[str, Brand] = {}

        # 3. Map code -> Product instance (chưa save)
        product_map: dict[str, Product] = {}
        image_map: dict[str, any] = {}

        for product_data in products_data:
            # --- tách brand_name ra ---
            brand_name = product_data.pop("brand_name", None)
            image = product_data.pop("image", None)

            brand = None
            if brand_name:
                if brand_name not in brand_cache:
                    brand_cache[brand_name], _ = Brand.objects.get_or_create(
                        name=brand_name
                    )
                brand = brand_cache[brand_name]

            product_code = product_data["code"]

            # --- tạo Product instance (chưa ghi DB) ---
            product_map[product_code] = Product(
                **product_data,
                brand=brand,
            )
            if image:
                image_map[product_code] = image

        # 4. Lấy các product đã tồn tại trong DB
        existing_products = Product.objects.filter(code__in=product_map.keys())

        existing_code_set = {product.code for product in existing_products}

        # 5. BULK CREATE (chỉ product chưa tồn tại)
        new_products = [
            product
            for code, product in product_map.items()
            if code not in existing_code_set
        ]

        Product.objects.bulk_create(new_products)

        # 6. BULK UPDATE (product đã tồn tại)
        for existing_product in existing_products:
            new_product_data = product_map[existing_product.code]

            existing_product.name = new_product_data.name
            existing_product.origin_price = new_product_data.origin_price
            existing_product.sale_price = new_product_data.sale_price
            existing_product.brand = new_product_data.brand
            existing_product.type = new_product_data.type
            existing_product.description = new_product_data.description
            existing_product.quantity_in_stock = new_product_data.quantity_in_stock

        Product.objects.bulk_update(
            existing_products,
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

        # --- UPLOAD IMAGE ---

        all_products = Product.objects.filter(code__in=product_map.keys())

        for product in all_products:
            image_object = image_map.get(product.code)
            if not image_object:
                continue

            buffer = BytesIO(image_object._data())
            buffer.seek(0)

            image_url = upload_file(
                buffer,
                folder="product_images/",
                public_id=f"product_{product.uid}_0",
                overwrite=True,
            )

            ProductImage.objects.update_or_create(
                product=product,
                is_main=True,
                defaults={"image_url": image_url["secure_url"]},
            )

        # 7. Trả về toàn bộ product (new + updated)
        return list(all_products)

    # =========================================
    # 4. UPLOAD IMAGE
    # =========================================

    @staticmethod
    @transaction.atomic
    def upload_image(product: Product, image_files: list):
        product_images = []
        for idx, image_file in enumerate(image_files):
            image_info = upload_file(
                file=image_file.file,
                folder="product_images/",
                public_id=f"product_{product.uid}_{idx}",
                overwrite=True,
            )

            product_image = ProductImage.objects.create(
                product=product,
                url=image_info["secure_url"],
                is_main=(idx == 0),
            )
            product_images.append(product_image)

        return product_images

    @staticmethod
    def get_all(payload: SearchFilterSortSchema):
        query = Q(deleted=False)
        if payload.search:
            query &= Q(name__icontains=payload.search)
        if payload.brand:
            query &= Q(brand__uid=payload.brand)
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
                    "image_fk_product",
                    queryset=ProductImage.objects.all(),
                    to_attr="images",
                )
            )
            .order_by(order_by_field)
        )

    @staticmethod
    def get_by_uid(uid: UUID):
        return (
            Product.objects.filter(uid=uid, deleted=False)
            .select_related("brand")
            .prefetch_related(
                Prefetch(
                    "image_fk_product",
                    queryset=ProductImage.objects.all(),
                    to_attr="images",
                ),
                Prefetch(
                    "review_fk_product",
                    queryset=Review.objects.select_related("user"),
                    to_attr="reviews",
                ),
            )
            .first()
        )

    @staticmethod
    def update(product: Product, payload: ProductRequestSchema):
        update_data = payload.dict(exclude_unset=True, exclude={"brand", "brand_name"})
        for field, value in update_data.items():
            setattr(product, field, value)
        if payload.brand_name:
            product.brand, _ = Brand.objects.get_or_create(name=payload.brand_name)
        product.save()
        return product

    @staticmethod
    def on_off(product: Product):
        product.deleted = not product.deleted
        product.save(update_fields=["deleted"])
        return product

    @staticmethod
    def delete_product(product: Product):
        product.delete()
        return True

    @staticmethod
    def generate_product_verify_code(product: Product, number_qrcode: int):
        return [generate_qrcode(product) for _ in range(number_qrcode)]

    @staticmethod
    def product_info(product: Product):
        return {
            "name": product.name,
            "code": product.code,
            "brand": getattr(product, "brand", None),
            "description": product.description,
        }

    @staticmethod
    @transaction.atomic
    def verify_qrcode(code: str):
        try:
            verify_code = (
                VerifyCode.objects.select_for_update()
                .select_related("product")
                .get(code=code)
            )
        except VerifyCode.DoesNotExist:
            return {
                "status": "FAKE",
                "message": "Mã QR không tồn tại. Có thể là hàng giả.",
                "product": None,
                "scan_count": 0,
            }

        if verify_code.scan_count >= verify_code.max_scan:
            return {
                "status": "FAKE",
                "message": "Mã QR đã bị quét vượt số lần cho phép. Có dấu hiệu hàng giả.",
                "product": ProductORM.product_info(product=verify_code.product),
                "scan_count": verify_code.scan_count,
            }

        if verify_code.scan_count > 0:
            verify_code.scan_count += 1
            verify_code.save(update_fields=["scan_count"])

            return {
                "status": "SCANNED",
                "message": "Mã QR đã được quét trước đó.",
                "product": ProductORM.product_info(product=verify_code.product),
                "scan_count": verify_code.scan_count,
            }

        verify_code.scan_count = 1
        verify_code.save(update_fields=["scan_count"])

        return {
            "status": "AUTHENTIC",
            "message": "Sản phẩm chính hãng.",
            "product": ProductORM.product_info(product=verify_code.product),
            "scan_count": verify_code.scan_count,
        }
