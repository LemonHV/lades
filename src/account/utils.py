import os
from datetime import timedelta

import jwt
from django.core.mail import send_mail
from django.utils.timezone import now

from account.models import AuthenticateToken, User


def generate_key(user: User, key_type: str) -> AuthenticateToken:
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        raise ValueError("SECRET_KEY is not set in environment variables")

    expires_minutes = int(os.environ.get("AUTHENTICATE_TOKEN_EXPIRES_IN", 1440))

    current_time = now()
    expires_at = current_time + timedelta(minutes=expires_minutes)

    payload = {
        "user_id": str(user.uid),
        "iat": int(current_time.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    token = jwt.encode(payload, secret_key, algorithm="HS256")

    token_object = AuthenticateToken(
        user=user,
        token=str(token),
        expires_at=expires_at,
    )
    token_object.save()
    return token_object


def get_key(user: User, key_type: str) -> AuthenticateToken:
    token = (
        AuthenticateToken.objects.filter(
            user=user, blacklisted_at__isnull=True, expires_at__gte=now()
        )
        .order_by("-created_at")
        .first()
    )
    return token or generate_key(user=user, key_type=key_type)


def send_verify_email(link: str, email: str, verify_type: str):
    logo_url = "https://img.freepik.com/premium-vector/hand-drawn-cosmetic-brushes-gentle-brush-stroke-grunge-style-sketch-cosmetic-illustration_484720-4254.jpg?w=2000"

    subjects = {
        "register": "Xác thực đăng ký tài khoản tại hệ thống Lades",
        "reset_password": "Đặt lại mật khẩu tài khoản Lades",
    }

    messages = {
        "register": f"Vui lòng xác thực đăng ký tài khoản bằng cách nhấp vào link bên dưới để xác thực: {link}",
        "reset_password": f"Bạn đã yêu cầu đặt lại mật khẩu. Truy cập link sau để tiếp tục: {link}",
    }

    contents = {
        "register": f"""
            Cảm ơn bạn đã đăng ký tài khoản tại <strong>Lades</strong>.<br><br>
            Vui lòng bấm vào đường dẫn bên dưới để xác nhận email và hoàn tất việc đăng ký.<br><br>
            <a href="{link}" style="color:#006241; text-decoration:underline;">Xác thực địa chỉ email</a><br><br>
            Sau khi hoàn thành đăng ký, bạn có thể mua sắm các sản phẩm và nhận ưu đãi hấp dẫn.<br><br>
            Trân trọng,<br><strong>Lades System</strong>
        """,
        "reset_password": f"""
            Chúng tôi đã nhận được yêu cầu <strong>đặt lại mật khẩu</strong> cho tài khoản tại <strong>Lades</strong>.<br><br>
            Vui lòng nhấn vào nút bên dưới để tạo mật khẩu mới.<br><br>
            <a href="{link}"
               style="display:inline-block; padding:12px 24px; background-color:#006241;
                      color:#ffffff; text-decoration:none; border-radius:4px;">
               Đặt lại mật khẩu
            </a><br><br>
            Link này chỉ có hiệu lực trong một khoảng thời gian nhất định.<br>
            Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.<br><br>
            Trân trọng,<br><strong>Lades System</strong>
        """,
    }

    html_message = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background-color:#ffffff; font-family: Arial, Helvetica, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="padding:40px 30px;">
                <tr>
                    <td align="center" style="padding-bottom:30px;">
                        <img src="{logo_url}" alt="Lades" width="120" style="display:block;">
                    </td>
                </tr>
                <tr>
                    <td style="color:#333333; font-size:14px; padding-bottom:20px;">
                        Xin chào bạn,
                    </td>
                </tr>
                <tr>
                    <td style="color:#333333; font-size:14px; line-height:1.6;">
                        {contents[verify_type]}
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
        subject=subjects[verify_type],
        message=messages[verify_type],
        from_email=os.environ.get("DEFAULT_FROM_EMAIL"),
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )


class SuccessMessage:
    # Auth – Register / Verify
    REGISTER = "Đăng ký thành công. Vui lòng kiểm tra email để xác thực tài khoản."
    RESET_PASSWORD_EMAIL_SENT = "Yêu cầu đặt lại mật khẩu thành công. Vui lòng kiểm tra email để xác thực tài khoản."

    # Auth – Login / Logout
    LOGIN = "Đăng nhập thành công."
    LOGOUT = "Đăng xuất thành công."

    # Password
    PASSWORD_RESET_SUCCESS = "Đặt lại mật khẩu thành công. Bạn có thể đăng nhập lại."
    PASSWORD_CHANGED = "Đặt lại mật khẩu thành công."

    # Shipping Address
    SHIPPING_INFO_DELETED = "Xóa thông tin giao hàng thành công"

    CART_ITEM_ADDED = "Thêm sản phẩm vào giỏ hàng thành công"
    CART_ITEM_UPDATED = "Cập nhật sản phẩm trong xóa hàng thành công"
    CART_ITEM_DELETED = "Xóa sản phẩm khỏi giỏ hàng thành công"
    DEFAULT_SHIPPING_INFO_SET = "Đặt thông tin giao hàng mặc định thành công"
    
    UPDATE_ORDER_STATUS_SUCCESS = "Cập nhật trạng thái đơn hàng thành công"
    CREATE_ORDER_SUCCESS = "Đặt hàng thành công"
