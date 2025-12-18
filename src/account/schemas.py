from ninja import Schema


class CredentialSchema(Schema):
    identifier: str
    password: str


class RegisterResponseSchema(Schema):
    identifier: str


class LoginResponseSchema(Schema):
    token: str


class LoginGoogleSchema(Schema):
    id_token: str


class LogoutSchema(Schema):
    token: str


class LogoutResponseSchema(Schema):
    success: bool
