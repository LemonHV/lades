import math
import os
import secrets
from io import BytesIO
from typing import List

import openpyxl
import qrcode
import requests
from cloudinary.uploader import upload
from django.http import HttpResponse
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from account.exceptions import BackendURLNotConfigured
from product.models import Product, VerifyCode


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


def generate_qrcode(product: Product):
    code = secrets.token_urlsafe(32)
    backend_url = os.environ.get("BACKEND_URL")
    if not backend_url:
        raise BackendURLNotConfigured
    link = f"{backend_url}/api/accounts/verify-qrcode?code={code}"
    qr = qrcode.make(link)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    result = upload_file(file=buffer, folder="qr_codes/", public_id=f"verify_{code}")

    verify_code = VerifyCode.objects.create(
        product=product,
        code=code,
        qr_url=result["secure_url"],
    )

    return verify_code


def generate_qrcode_pdf(verify_codes):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    cols = 10
    gap = 0.5 * mm
    padding = 5 * mm

    usable_width = width - 2 * padding
    usable_height = height - 2 * padding

    size = (usable_width - (cols - 1) * gap) / cols

    rows = math.floor((usable_height + gap) / (size + gap))

    x_start = padding
    y_start = height - padding - size

    x = x_start
    y = y_start
    count = 0

    for vc in verify_codes:
        if not vc.qr_url:
            continue

        r = requests.get(vc.qr_url, timeout=10)
        if r.status_code != 200:
            continue

        if not r.headers.get("Content-Type", "").startswith("image/"):
            continue

        image = ImageReader(BytesIO(r.content))
        c.drawImage(image, x, y, size, size, preserveAspectRatio=True)

        x += size + gap
        count += 1

        if count % cols == 0:
            x = x_start
            y -= size + gap

        if count % (cols * rows) == 0:
            c.showPage()
            x = x_start
            y = y_start

    c.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="qr_codes.pdf"'
    return response
