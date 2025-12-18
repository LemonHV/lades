from http import HTTPStatus

from ninja.errors import HttpError

from account.models import User

from .types import AuthenticatedRequest


class IsUser:
    def __call__(self, request: AuthenticatedRequest):
        user: User = request.user

        if user.is_staff:
            raise HttpError(
                HTTPStatus.FORBIDDEN,
                "Admin is not allowed to access this resource",
            )


class IsAdmin:
    def __call__(self, request: AuthenticatedRequest):
        user: User = request.user

        if not user.is_staff:
            raise HttpError(
                HTTPStatus.FORBIDDEN,
                "Admin permission required",
            )
