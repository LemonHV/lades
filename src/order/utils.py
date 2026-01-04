import string
import random
import os
from reportlab.platypus import Paragraph
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A6
from reportlab.graphics.barcode import code128
from io import BytesIO
from enum import unique
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import TextChoices
from django.core.mail import send_mail


@unique
class OrderStatus(TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    SHIPPING = "SHIPPING", "Shipping"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


@unique
class PaymentStatus(TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


def generate_code(length=20):
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


def register_fonts():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROBOTO_R_PATH = os.path.join(BASE_DIR, "Roboto-Regular.ttf")
    ROBOTO_B_PATH = os.path.join(BASE_DIR, "Roboto-Bold.ttf")
    pdfmetrics.registerFont(TTFont("Roboto", ROBOTO_R_PATH))
    pdfmetrics.registerFont(TTFont("Roboto-Bold", ROBOTO_B_PATH))


def get_logo_path():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(BASE_DIR, "static/logo.jpg")


def count_quantity(order_items):
    quantity = 0
    for oi in order_items:
        quantity += oi.quantity
    return quantity


def generate_order_bill(order, order_items):
    """
    Generate A6 shipping order bill (PDF)
    Layout:
    - Header: Shop name + logo + barcode
    - Sender / Receiver info (2 columns)
    - Product list
    - COD amount + signature area
    """

    buffer = BytesIO()
    register_fonts()
    c = canvas.Canvas(buffer, pagesize=A6)
    width, height = A6

    # ========================
    # CONFIG
    # ========================
    padding = 5 * mm
    margin = 2 * mm
    usable_width = width - 2 * padding

    # ========================
    # PAGE BORDER
    # ========================
    c.rect(0.5 * mm, 0.5 * mm, width - 1 * mm, height - 1 * mm)

    origin_x = padding
    origin_y = height - padding

    # ==================================================
    # HEADER: SHOP NAME + LOGO + BARCODE
    # ==================================================
    header_y = origin_y
    shop_name = "Giao hàng nhanh"

    c.setFont("Roboto-Bold", 12)
    c.drawString(origin_x, header_y, shop_name)

    # --- Center logo under shop name
    text_width = c.stringWidth(shop_name, "Roboto-Bold", 12)
    text_center_x = origin_x + text_width / 2

    logo_path = get_logo_path()
    logo_width = 20 * mm
    logo_height = 12 * mm

    c.drawImage(
        ImageReader(logo_path),
        text_center_x - logo_width / 2,
        header_y - logo_height - 4,
        width=logo_width,
        height=logo_height,
        mask="auto",
    )

    # --- Barcode (right side)
    barcode = code128.Code128(
        order.code,
        barHeight=8 * mm,
        barWidth=0.15 * mm,
    )

    barcode_x = width - padding - barcode.width
    barcode_y = header_y - barcode.height + 3
    barcode.drawOn(c, barcode_x, barcode_y)

    c.setFont("Roboto", 8)
    c.drawString(barcode_x, barcode_y - 10, f"Mã đơn hàng: {order.code}")

    # --- Divider below header
    c.setDash(3, 2)
    c.line(padding, barcode_y - 20, width - padding, barcode_y - 20)
    c.setDash()

    # ==================================================
    # SENDER & RECEIVER INFO (2 COLUMNS)
    # ==================================================
    info_y = barcode_y - 30
    left_x = origin_x
    right_x = origin_x + usable_width / 2 + margin

    # --- Text styles
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    normal_style.fontName = "Roboto"
    normal_style.fontSize = 9
    normal_style.leading = 11

    # --- Sender
    c.setFont("Roboto-Bold", 10)
    c.drawString(left_x, info_y, "Người gửi:")

    sender_para = Paragraph(
        "Lades Beauty<br/>127/25/2E Cô Giang, P1, Phú Nhuận",
        normal_style,
    )
    _, sender_h = sender_para.wrap(usable_width / 2 - 2 * margin, 50 * mm)
    sender_para.drawOn(c, left_x, info_y - 12 - sender_h + 11)

    # --- Receiver
    c.drawString(right_x, info_y, "Người nhận:")

    receiver_para = Paragraph(
        f"{order.name}<br/>{order.address}<br/>SĐT: {order.phone}",
        normal_style,
    )
    _, receiver_h = receiver_para.wrap(usable_width / 2 - 2 * margin, 50 * mm)
    receiver_para.drawOn(c, right_x, info_y - 12 - receiver_h + 11)

    # --- Vertical divider
    c.setDash(3, 2)
    c.line(
        origin_x + usable_width / 2,
        info_y,
        origin_x + usable_width / 2,
        info_y - max(sender_h, receiver_h) - 5,
    )
    c.setDash()

    # --- Horizontal divider
    items_start_y = info_y - max(sender_h, receiver_h) - 5
    c.setDash(3, 2)
    c.line(padding, items_start_y, width - padding, items_start_y)
    c.setDash()

    # ==================================================
    # PRODUCT LIST
    # ==================================================
    text_y = items_start_y - 10
    c.setFont("Roboto-Bold", 10)
    c.drawString(
        left_x,
        text_y,
        f"Nội dung sản phẩm: (Tổng SL sản phẩm: {count_quantity(order_items)})",
    )

    text_y -= 8

    item_style = styles["Normal"]
    item_style.fontName = "Roboto"
    item_style.fontSize = 9
    item_style.leading = 12

    for index, oi in enumerate(order_items, start=1):
        para = Paragraph(
            f"{index}. {oi.product.name} - SL: {oi.quantity}",
            item_style,
        )
        _, para_h = para.wrap(usable_width - 10, 100)
        para.drawOn(c, left_x + 5, text_y - para_h)
        text_y -= para_h + 4

    # ==================================================
    # FOOTER DIVIDER
    # ==================================================
    footer_y = padding + 60
    c.setDash(3, 2)
    c.line(padding, footer_y, width - padding, footer_y)
    c.setDash()

    # ==================================================
    # COD AMOUNT & SIGNATURE AREA
    # ==================================================
    half_width = usable_width / 2
    right_center_x = padding + half_width + half_width / 2

    # --- Labels
    label_y = footer_y - 12
    c.setFont("Roboto", 9)
    c.drawString(padding, label_y, "Tiền thu Người nhận:")
    c.drawCentredString(right_center_x, label_y, "Khối lượng tối đa: 1000g")

    # --- Signature title
    sign_title_y = label_y - 10
    c.setFont("Roboto-Bold", 9)
    c.drawCentredString(right_center_x, sign_title_y, "Chữ ký người nhận")

    # --- Signature note (auto wrap)
    note_y = sign_title_y - 10
    c.setFont("Roboto", 7)

    note_lines = [
        "(Xác nhận hàng nguyên vẹn, không móp méo,",
        "bể/vỡ)",
    ]
    for i, line in enumerate(note_lines):
        c.drawCentredString(right_center_x, note_y - i * 9, line)

    # --- Signature line
    sign_line_y = note_y - len(note_lines) * 9 - 12
    c.line(
        right_center_x - (half_width - 12 * mm) / 2,
        sign_line_y,
        right_center_x + (half_width - 12 * mm) / 2,
        sign_line_y,
    )

    # --- COD amount
    c.setFont("Roboto-Bold", 18)
    c.drawString(padding, note_y, f"{order.total_amount:,} VND")

    # --- Delivery instruction
    c.setFont("Roboto-Bold", 9)
    c.drawString(padding, sign_line_y - 6, "Chỉ dẫn giao hàng: Đồng kiểm")

    # ========================
    # EXPORT PDF
    # ========================
    c.showPage()
    c.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="order_{order.code}.pdf"'
    return response


def send_order_confirmation_email(order, email, link=None):
    logo_url = "https://img.freepik.com/premium-vector/hand-drawn-cosmetic-brushes-gentle-brush-stroke-grunge-style-sketch-cosmetic-illustration_484720-4254.jpg?w=2000"

    # Format ngày đẹp: dd/mm/yyyy HH:MM
    order_date = timezone.localtime(order.order_date).strftime("%d/%m/%Y %H:%M")

    subject = f"Xác nhận đơn hàng {order.code} tại Lades"
    message = f"Đơn hàng {order.code} của bạn đã được đặt thành công. Xem chi tiết: {link or ''}"

    # Build danh sách sản phẩm thành HTML table đẹp
    items_html = ""
    for item in getattr(order, "order_items", order.order_item_fk_order.all()):
        items_html += f"""
            <tr>
                <td style="padding:6px 8px; border:1px solid #ddd; font-size:14px; max-width:250px; word-break:break-word;">{item.product.name}</td>
                <td style="padding:6px 8px; border:1px solid #ddd; text-align:center; font-size:14px;">{item.quantity}</td>
                <td style="padding:6px 8px; border:1px solid #ddd; text-align:right; font-size:14px; white-space:nowrap;">{item.total_price:,} VNĐ</td>
            </tr>
        """

    # Thêm phí vận chuyển và tổng tiền vào cuối bảng
    shipping_fee = getattr(order, "shipping_fee", 0)
    total_amount = getattr(order, "total_amount", 0) + shipping_fee
    items_html += f"""
        <tr>
            <td colspan="2" style="padding:6px 8px; border:1px solid #ddd; text-align:right; font-weight:bold;">Phí vận chuyển</td>
            <td style="padding:6px 8px; border:1px solid #ddd; text-align:right; font-weight:bold;">{shipping_fee:,} VNĐ</td>
        </tr>
        <tr>
            <td colspan="2" style="padding:6px 8px; border:1px solid #ddd; text-align:right; font-weight:bold;">Tổng cộng</td>
            <td style="padding:6px 8px; border:1px solid #ddd; text-align:right; font-weight:bold;">{total_amount:,} VNĐ</td>
        </tr>
    """

    html_message = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background-color:#f8f8f8; font-family: Arial, Helvetica, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="padding:40px; background-color:#ffffff; border-radius:8px; box-shadow:0 0 10px rgba(0,0,0,0.1);">
                <tr>
                    <td align="center" style="padding-bottom:30px;">
                        <img src="{logo_url}" alt="Lades" width="120" style="display:block;">
                    </td>
                </tr>
                <tr>
                    <td style="color:#333333; font-size:16px; padding-bottom:20px;">
                        Xin chào <strong>{order.name}</strong>,
                    </td>
                </tr>
                <tr>
                    <td style="color:#333333; font-size:14px; line-height:1.6;">
                        Đơn hàng của bạn đã được đặt thành công!<br><br>
                        <strong>Mã đơn hàng:</strong> {order.code}<br>
                        <strong>Ngày đặt:</strong> {order_date}<br>
                        <strong>Tổng thanh toán:</strong> {order.total_amount + order.shipping_fee:,} VNĐ<br><br>

                        <strong>Danh sách sản phẩm:</strong>
                        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse; margin-top:10px;">
                            <thead style="background-color:#006241; color:#ffffff;">
                                <tr>
                                    <th style="padding:8px; border:1px solid #ddd; text-align:left;">Sản phẩm</th>
                                    <th style="padding:8px; border:1px solid #ddd; text-align:center;">Số lượng</th>
                                    <th style="padding:8px; border:1px solid #ddd; text-align:right;">Thành tiền</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items_html}
                            </tbody>
                        </table><br>

                        {f'<a href="{link}" style="display:inline-block;padding:12px 24px;background-color:#006241;color:#ffffff;text-decoration:none;border-radius:4px;">Xem chi tiết đơn hàng</a>' if link else ""}
                    </td>
                </tr>
                <tr>
                    <td style="padding:30px 0;"><hr style="border:none; border-top:1px solid #dddddd;"></td>
                </tr>
                <tr>
                    <td style="padding-top:20px; font-size:12px; color:#999999; line-height:1.5;">
                        Email này được gửi tự động, vui lòng không phản hồi.<br>
                        © 2025 Lades. Bảo lưu mọi quyền.
                    </td>
                </tr>
            </table>
            </td>
        </tr>
        </table>
    </body>
    </html>
    """

    send_mail(
        subject=subject,
        message=message,
        from_email=os.environ.get("DEFAULT_FROM_EMAIL"),
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )
