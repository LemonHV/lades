from ninja import Schema


class CredentialSchema(Schema):
    email: str
    password: str


class RegisterResponseSchema(Schema):
    email: str


class LoginResponseSchema(Schema):
    token: str | None


class LoginGoogleSchema(Schema):
    id_token: str


class LogoutSchema(Schema):
    token: str


class LogoutResponseSchema(Schema):
    success: bool
