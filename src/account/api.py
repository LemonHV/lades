import os

from django.shortcuts import redirect

from account.services import AccountService
from router.authenticate import AuthBear
from router.controller import Controller, api, get, post, put

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
        self.service.register(email=payload.email, password=payload.password)
        return RegisterResponseSchema(email=payload.email)

    @get("/verify-email/{token}")
    def verify_email(self, token: str):
        self.service.verify_email(token=token)
        frontend_url = os.environ.get("FRONTEND_URL")
        if not frontend_url:
            raise RuntimeError("Frontend url is not set")
        return redirect(frontend_url)

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
