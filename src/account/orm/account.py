import os
from datetime import timedelta

import jwt
from django.utils.timezone import now

from account.models import AuthenticateToken, User


class AccountORM:
    # REGISTER #
    @staticmethod
    def register(identifier: str, password: str) -> User | None:
        if User.objects.filter(identifier=identifier).exists():
            return None
        user = User(identifier=identifier)
        user.set_password(password)
        user.save()
        return user

    # LOGIN WITH CREDENTIAL #
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

    @staticmethod
    def login_with_credential(identifier: str, password: str) -> str | None:
        try:
            user = User.objects.get(identifier=identifier)
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
    def login_with_google(google_id: str) -> str:
        user = User.objects.filter(google_id=google_id).first()
        if user is None:
            user = User.objects.create(
                google_id=google_id,
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
