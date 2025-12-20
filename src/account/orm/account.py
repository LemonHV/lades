import os
from datetime import timedelta

import jwt
from django.core.mail import send_mail
from django.utils.timezone import now

from account.models import AuthenticateToken, User


class AccountORM:
    @staticmethod
    def generate_key(user: User) -> AuthenticateToken:
        current_time = now()
        expires_minutes = int(os.environ.get("AUTHENTICATE_TOKEN_EXPIRES_IN", 1440))
        payload = {
            "user_id": str(user.uid),
            "iat": int(current_time.timestamp()),
            "exp": int((current_time + timedelta(minutes=expires_minutes)).timestamp()),
        }
        token = jwt.encode(payload, os.environ.get("SECRET_KEY"), algorithm="HS256")
        token_object = AuthenticateToken(
            user=user,
            token=str(token),
            expires_at=current_time + timedelta(minutes=expires_minutes),
        )
        token_object.save()
        return token_object

    @staticmethod
    def get_key(user: User) -> AuthenticateToken:
        token = (
            AuthenticateToken.objects.filter(
                user=user, blacklisted_at__isnull=True, expires_at__gte=now()
            )
            .order_by("-created_at")
            .first()
        )
        if token:
            return token
        return AccountORM.generate_key(user=user)

    # REGISTER #
    @staticmethod
    def register(email: str, password: str) -> User | None:
        if User.objects.filter(email=email).exists():
            return None
        user = User(email=email, is_active=False)
        user.set_password(password)
        user.save()
        token_object = AccountORM.get_key(user=user)

        link = f"http://localhost:8000/verify-email/?token={token_object.token}"
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0; padding:0; background-color:#ffffff; font-family: Arial, Helvetica, sans-serif;">
            <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
                <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="padding:40px 30px;">

                    <!-- LOGO -->
                    <tr>
                    <td align="center" style="padding-bottom:30px;">
                        <img src="https://img.freepik.com/premium-vector/hand-drawn-cosmetic-brushes-gentle-brush-stroke-grunge-style-sketch-cosmetic-illustration_484720-4254.jpg?w=2000"
                            alt="Lades"
                            width="120"
                            style="display:block;">
                    </td>
                    </tr>

                    <!-- GREETING -->
                    <tr>
                    <td style="color:#333333; font-size:14px; padding-bottom:20px;">
                        Xin chào bạn,
                    </td>
                    </tr>

                    <!-- MAIN CONTENT -->
                    <tr>
                    <td style="color:#333333; font-size:14px; line-height:1.6;">
                        Cảm ơn bạn đã đăng ký tài khoản tại <strong>Lades</strong>.
                        <br><br>

                        Vui lòng bấm vào đường dẫn bên dưới để xác nhận email và hoàn tất việc đăng ký.
                        <br><br>

                        <a href="{link}" style="color:#006241; text-decoration:underline;">
                        Xác thực địa chỉ email
                        </a>
                        <br><br>

                        Sau khi hoàn thành đăng ký tài khoản, bạn có thể thoải mái mua sắm những bộ cọ tuyệt đẹp.
                        Cùng với đó là những ưu đãi hấp dẫn mà hãng <strong>Lades</strong> mang đến.
                        Hãy nhanh tay mua sắm nào!
                        <br><br>

                        Trân trọng,<br>
                        <strong>Lades System</strong>
                    </td>
                    </tr>


                    <!-- DIVIDER -->
                    <tr>
                    <td style="padding:30px 0;">
                        <hr style="border:none; border-top:1px solid #dddddd;">
                    </td>
                    </tr>

                    <!-- FOOTER -->
                    <tr>
                    <td style="padding-top:20px; font-size:12px; color:#999999; line-height:1.5;">
                        Email này được gửi tự động, vui lòng không phản hồi.<br>
                        Nếu bạn không thực hiện yêu cầu đăng ký, hãy bỏ qua email này.<br><br>
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
        if not user.email:
            raise ValueError("User không có email")
        send_mail(
            subject="Xác thực đăng ký tài khoản tại hệ thống Lades",
            message=f"Vui lòng xác thực đăng ký tài khoản bằng cách nhấp vào link bên dưới để xác thực xác thực: {link}",
            from_email=os.environ.get("DEFAULT_FROM_EMAIL"),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return user

    @staticmethod
    def verify_email(token: str):
        token_object = (
            AuthenticateToken.objects.filter(
                token=token,
                blacklisted_at__isnull=True,
                expires_at__gte=now(),
            )
            .order_by("-created_at")
            .first()
        )
        if token_object is None:
            return "Link không hợp lệ hoặc đã dùng"

        user = token_object.user
        user.is_active = True
        user.save()

        token_object.blacklisted_at = now()
        token_object.save()

        new_token_object = AccountORM.get_key(user=user)
        return new_token_object.token

    # LOGIN WITH CREDENTIAL #

    @staticmethod
    def login_with_credential(email: str, password: str) -> str | None:
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        if not user.is_active or not user.check_password(password):
            return None
        token_object = AccountORM.get_key(user=user)
        return token_object.token

    # LOGOUT #
    @staticmethod
    def logout(token: str):
        try:
            token_object = AuthenticateToken.objects.get(token=token)
        except AuthenticateToken.DoesNotExist:
            return False
        token_object.blacklisted_at = now()
        token_object.save()
        return True

    @staticmethod
    def login_with_google(google_id: str, email: str, name: str) -> str:
        user = User.objects.filter(google_id=google_id).first()
        if user is None:
            user = User.objects.create(
                google_id=google_id,
                email=email,
                name=name,
                is_active=True,
            )
        token = (
            AuthenticateToken.objects.filter(
                user=user,
                blacklisted_at__isnull=True,
                expires_at__gte=now(),
            )
            .order_by("-created_at")
            .first()
        )
        if token:
            return token.token

        return AccountORM.get_key(user=user).token
