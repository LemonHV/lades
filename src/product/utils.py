from io import BytesIO
from typing import List

import openpyxl
from cloudinary.uploader import upload
from openpyxl.utils import get_column_letter


PRODUCT_HEADERS = [
    "Tên sản phẩm",
    "Mã sản phẩm",
    "Giá gốc",
    "Giá bán",
    "Thương hiệu",
    "Phân loại",
    "Mô tả",
    "Số lượng trong kho",
]


def build_product_workbook() -> BytesIO:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Danh sách sản phẩm"

    ws.append(PRODUCT_HEADERS)
    for index in range(1, len(PRODUCT_HEADERS) + 1):
        ws.column_dimensions[get_column_letter(index)].width = 25

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def load_product_infomation(product_file) -> List[dict]:
    workbook = openpyxl.load_workbook(product_file)
    sheet = workbook.active

    products = []

    for row_index, row in enumerate(
        sheet.iter_rows(min_row=2, values_only=True),
        start=2,
    ):
        (
            name,
            code,
            origin_price,
            sale_price,
            brand_name,
            type_,
            description,
            quantity_in_stock,
        ) = row

        if not all([name, code, origin_price, sale_price, type_, quantity_in_stock]):
            continue

        product_data = {
            "name": name,
            "code": code,
            "origin_price": origin_price,
            "sale_price": sale_price,
            "brand_name": brand_name,
            "type": type_,
            "description": description or "",
            "quantity_in_stock": quantity_in_stock,
        }

        products.append(product_data)

    return products


def upload_file(file, folder: str, public_id: str, overwrite: bool = True) -> dict:
    """
    Upload 1 file lên cloud storage (Cloudinary).
    Trả về dict kết quả chứa URL, public_id, ...
    """
    return upload(
        file,
        folder=folder,
        public_id=public_id,
        overwrite=overwrite,
    )
