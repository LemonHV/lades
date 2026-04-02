from typing import Optional
from uuid import UUID

from django.utils.timezone import now

from account.models import AuthenticateToken, User


class AccountORM:
    @staticmethod
    def get_user_by_uid(uid: UUID) -> Optional[User]:
        return User.objects.filter(uid=uid).first()

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        normalized_email = User.objects.normalize_email_value(email)
        return User.objects.filter(email=normalized_email).first()

    @staticmethod
    def get_user_by_google_id(google_id: str) -> Optional[User]:
        return User.objects.filter(google_id=google_id).first()

    @staticmethod
    def create_user(
        email: str, password: str | None = None, is_active: bool = False, **extra_fields
    ) -> User:
        normalized_email = User.objects.normalize_email_value(email)

        user = User(email=normalized_email, is_active=is_active, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()
        return user

    @staticmethod
    def update_user_password(user: User, new_password: str) -> User:
        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])
        return user

    @staticmethod
    def activate_user(user: User) -> User:
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active", "updated_at"])
        return user

    @staticmethod
    def update_user_info(user: User, **fields) -> User:
        updated_fields: list[str] = []

        for key, value in fields.items():
            if value is None or not hasattr(user, key):
                continue

            if isinstance(value, str):
                value = value.strip()

            if getattr(user, key) != value:
                setattr(user, key, value)
                updated_fields.append(key)

        if updated_fields:
            updated_fields.append("updated_at")
            user.save(update_fields=updated_fields)

        return user

    @staticmethod
    def get_token(token: str) -> Optional[AuthenticateToken]:
        return (
            AuthenticateToken.objects.select_related("user")
            .filter(token=token)
            .order_by("-created_at")
            .first()
        )

    @staticmethod
    def get_valid_token(token: str, key_type: str) -> Optional[AuthenticateToken]:
        return (
            AuthenticateToken.objects.select_related("user")
            .filter(
                token=token,
                key_type=key_type,
                blacklisted_at__isnull=True,
                expires_at__gte=now(),
            )
            .order_by("-created_at")
            .first()
        )

    @staticmethod
    def blacklist_token(token_object: AuthenticateToken) -> None:
        if token_object.blacklisted_at is None:
            token_object.blacklisted_at = now()
            token_object.save(update_fields=["blacklisted_at", "updated_at"])
