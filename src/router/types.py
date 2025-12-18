from django.http import HttpRequest

from account.models import AuthenticateToken, User


class AuthenticatedRequest(HttpRequest):
    user: User
    token: AuthenticateToken
