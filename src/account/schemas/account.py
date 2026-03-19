from typing import Optional
from uuid import UUID

from ninja import Schema


class MessageResponseSchema(Schema):
    message: str


class TokenResponseSchema(Schema):
    token: str


class LoginSchema(Schema):
    email: str
    password: str


class GoogleLoginSchema(Schema):
    id_token: str


class LoginResponseSchema(TokenResponseSchema):
    is_staff: bool


class ChangePasswordSchema(Schema):
    old_password: str
    new_password: str


class ForgotPasswordSchema(Schema):
    email: str


class ResetPasswordConfirmSchema(Schema):
    token: str
    new_password: str


class UserInfoSchema(Schema):
    uid: UUID
    name: Optional[str] = None
    email: str
    is_staff: bool


class UpdateUserInfoSchema(Schema):
    name: str