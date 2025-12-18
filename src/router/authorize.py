from ninja.errors import HttpError

from account.models import User

from .types import AuthenticatedRequest


class IsUser:
    def has_permission(self, request: AuthenticatedRequest, **kwargs):
        user: User = request.user

        if user.is_staff:
            raise HttpError(403, "Not allowed")
        return True


class IsAdmin:
    def has_permission(self, request: AuthenticatedRequest, **kwargs):
        user = request.user
        if not user.is_staff:
            raise HttpError(403, "Not allowed")
        return True
