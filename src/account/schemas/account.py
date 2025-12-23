from typing import Optional
from uuid import UUID

from ninja import Schema


# Message
class MessageResponseSchema(Schema):
    message: str


# Login
class CredentialSchema(Schema):
    email: str
    password: str


class LoginResponseSchema(Schema):
    message: str
    token: str


class LoginGoogleSchema(Schema):
    id_token: str


# Change/Reset Password
class ChangePasswordSchema(Schema):
    old_password: str
    new_password: str


class ResetPasswordSchema(Schema):
    email: str


class SavePasswordSchema(Schema):
    token: str
    new_password: str


# User Info
class UserInfoSchema(Schema):
    uid: UUID
    name: Optional[str] = None
    email: str
    is_staff: bool


class UpdateInfoSchema(Schema):
    name: str
