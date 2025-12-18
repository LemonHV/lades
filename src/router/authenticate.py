from http import HTTPStatus

from django.utils.timezone import now
from ninja.security import HttpBearer

from account.models import AuthenticateToken
from exceptions.exception import APIException

from .types import AuthenticatedRequest


class InvalidOrExpiredToken(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "INVALID_OR_EXPIRED_TOKEN"
    message = "Invalid or expired token"


class AuthBear(HttpBearer):
    @staticmethod
    def verify_token(token: str) -> AuthenticateToken:
        token_object = AuthenticateToken.objects.filter(
            token=token, blacklisted_at__isnull=True, expires_at__gte=now()
        ).first()

        if not token_object:
            raise InvalidOrExpiredToken

        return token_object

    @classmethod
    def authenticate(cls, request: AuthenticatedRequest, token: str):  # type: ignore
        authenticate_token = cls.verify_token(token=token)

        request.user = authenticate_token.user
        request.token = authenticate_token

        return request
