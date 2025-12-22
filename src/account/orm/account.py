import os

from django.utils.timezone import now

from account.exceptions import (
    BackendURLNotConfigured,
    EmailNotExists,
    InvalidOrExpiredToken,
)
from account.models import AuthenticateToken, User
from account.utils import get_key, send_verify_email


class AccountORM:
    # =========================================
    # 1. REGISTER & VERIFY EMAIL
    # =========================================
    @staticmethod
    def register(email: str, password: str) -> None:
        user = User(email=email, is_active=False)
        user.set_password(password)
        user.save()
        token_object = get_key(user=user)

        backend_url = os.environ.get("BACKEND_URL")
        if not backend_url:
            raise BackendURLNotConfigured

        link = f"{backend_url}/api/account/verify-email-register/{token_object.token}"

        send_verify_email(link=link, email=user.email, verify_type="register")

    @staticmethod
    def verify_email_register(token: str) -> None:
        token_object = (
            AuthenticateToken.objects.select_related("user")
            .filter(
                token=token,
                blacklisted_at__isnull=True,
                expires_at__gte=now(),
            )
            .order_by("-created_at")
            .first()
        )

        if not token_object:
            raise InvalidOrExpiredToken

        user = token_object.user
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])

        token_object.blacklisted_at = now()
        token_object.save(update_fields=["blacklisted_at"])

    # =========================================
    # 2. LOGN & GET TOKEN
    # =========================================

    @staticmethod
    def login_with_credential(user: User) -> str:
        authenticate_token = get_key(user=user)
        return authenticate_token.token

    @staticmethod
    def login_with_google(google_id: str, email: str, name: str) -> str:
        user = User.objects.filter(google_id=google_id).first()

        if not user:
            user = User.objects.create(
                google_id=google_id,
                email=email,
                name=name,
                is_active=True,
            )

        return get_key(user=user).token

    # =========================================
    # 3. LOGOUT
    # =========================================

    @staticmethod
    def logout(token: str) -> None:
        try:
            token_object = AuthenticateToken.objects.get(
                token=token,
                blacklisted_at__isnull=True,
            )
        except AuthenticateToken.DoesNotExist:
            raise InvalidOrExpiredToken

        token_object.blacklisted_at = now()
        token_object.save(update_fields=["blacklisted_at"])

    # =========================================
    # 4. CHANGE PASSWORD
    # =========================================

    @staticmethod
    def change_password(user: User, new_password: str):
        user.set_password(new_password)
        user.save(update_fields=["password"])

    # =========================================
    # 5. RESET PASSWORD
    # =========================================

    @staticmethod
    def reset_password(email: str) -> None:
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise EmailNotExists

        backend_url = os.environ.get("BACKEND_URL")
        if not backend_url:
            raise BackendURLNotConfigured

        token_object = get_key(user=user)

        link = f"{backend_url}/api/account/verify-email-reset-password/{token_object.token}"

        send_verify_email(
            link=link,
            email=user.email,
            verify_type="reset_password",
        )

    @staticmethod
    def verify_email_reset_password(token: str) -> User:
        token_object = (
            AuthenticateToken.objects.select_related("user")
            .filter(
                token=token,
                blacklisted_at__isnull=True,
                expires_at__gte=now(),
            )
            .order_by("-created_at")
            .first()
        )

        if not token_object:
            raise InvalidOrExpiredToken

        user = token_object.user
        token_object.blacklisted_at = now()
        token_object.save(update_fields=["blacklisted_at"])

        return user

    @staticmethod
    def save_password(token: str, new_password: str):
        token_object = (
            AuthenticateToken.objects.select_related("user")
            .filter(
                token=token,
                blacklisted_at__isnull=True,
                expires_at__gte=now(),
            )
            .order_by("-created_at")
            .first()
        )
        if not token_object:
            raise InvalidOrExpiredToken
        user = token_object.user
        user.set_password(new_password)
        user.save(update_fields=["password"])
        token_object.blacklisted_at = now()

        token_object.save(update_fields=["blacklisted_at"])
