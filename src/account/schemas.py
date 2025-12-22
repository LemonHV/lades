from ninja import Schema


class MessageResponseSchema(Schema):
    message: str


class CredentialSchema(Schema):
    email: str
    password: str


class LoginResponseSchema(Schema):
    message: str
    token: str


class LoginGoogleSchema(Schema):
    id_token: str


class SuccessSchema(Schema):
    success: bool


class ChangePasswordSchema(Schema):
    old_password: str
    new_password: str


class ResetPasswordSchema(Schema):
    email: str


class SavePasswordSchema(Schema):
    token: str
    new_password: str
