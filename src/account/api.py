from account.services import AccountService
from router.authenticate import AuthBear
from router.controller import Controller, api, post, put

from .schemas import (
    CredentialSchema,
    LoginGoogleSchema,
    LoginResponseSchema,
    LogoutResponseSchema,
    LogoutSchema,
    RegisterResponseSchema,
)


@api(prefix_or_class="account", tags=["Account"], auth=None)
class AccountAPI(Controller):
    def __init__(self, service: AccountService):
        self.service = service

    @post("/register", response=RegisterResponseSchema)
    def register(self, payload: CredentialSchema):
        return self.service.register(email=payload.email, password=payload.password)

    @post("/verify-email/{token}", response=LoginResponseSchema)
    def verify_email(self, token: str):
        return LoginResponseSchema(token=self.service.verify_email(token=token))

    @post("/login-credential", response=LoginResponseSchema)
    def login_with_credential(self, payload: CredentialSchema):
        token = self.service.login_with_credential(
            email=payload.email, password=payload.password
        )
        return LoginResponseSchema(token=token)

    @put("/logout", auth=AuthBear(), response=LogoutResponseSchema)
    def logout(self, payload: LogoutSchema):
        return LogoutResponseSchema(success=self.service.logout(token=payload.token))

    @post("/login-google", response=LoginResponseSchema)
    def login_with_google(self, payload: LoginGoogleSchema):
        token = self.service.login_with_google(id_token=payload.id_token)
        return LoginResponseSchema(token=token)
