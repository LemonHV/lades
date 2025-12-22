import os
from urllib.parse import quote

from django.shortcuts import redirect

from account.exceptions import FrontendURLNotConfigured
from account.services import AccountService
from account.utils import SuccessMessage, get_key
from router.authenticate import AuthBear
from router.controller import Controller, api, get, post, put
from router.types import AuthenticatedRequest

from .schemas import (
    ChangePasswordSchema,
    CredentialSchema,
    LoginGoogleSchema,
    LoginResponseSchema,
    MessageResponseSchema,
    ResetPasswordSchema,
    SavePasswordSchema,
)


@api(prefix_or_class="account", tags=["Account"], auth=None)
class AccountAPI(Controller):
    def __init__(self, service: AccountService):
        self.service = service

    @post("/register", response=MessageResponseSchema)
    def register(self, payload: CredentialSchema):
        self.service.register(email=payload.email, password=payload.password)
        return MessageResponseSchema(message=SuccessMessage.REGISTER)

    @get("/verify-email-register/{token}")
    def verify_email_register(self, token: str):
        self.service.verify_email_register(token=token)
        frontend_url = os.environ.get("FRONTEND_REGISTER_URL")
        if not frontend_url:
            raise FrontendURLNotConfigured
        return redirect(frontend_url)

    @post("/login-credential", response=LoginResponseSchema)
    def login_with_credential(self, payload: CredentialSchema):
        token = self.service.login_with_credential(
            email=payload.email, password=payload.password
        )
        return LoginResponseSchema(message=SuccessMessage.LOGIN, token=token)

    @post("/login-google", response=LoginResponseSchema)
    def login_with_google(self, payload: LoginGoogleSchema):
        token = self.service.login_with_google(id_token=payload.id_token)
        return LoginResponseSchema(token=token, message=SuccessMessage.LOGIN)

    @put("/logout", auth=AuthBear(), response=MessageResponseSchema)
    def logout(self, request: AuthenticatedRequest):
        self.service.logout(token=request.token.token)
        return MessageResponseSchema(message=SuccessMessage.LOGOUT)

    @put("/change-password", auth=AuthBear(), response=MessageResponseSchema)
    def change_password(
        self, request: AuthenticatedRequest, payload: ChangePasswordSchema
    ):
        self.service.change_password(
            user=request.user,
            old_password=payload.old_password,
            new_password=payload.new_password,
        )
        return MessageResponseSchema(message=SuccessMessage.PASSWORD_CHANGED)

    @post("/reset-password")
    def reset_password(self, payload: ResetPasswordSchema):
        self.service.reset_password(email=payload.email)
        return MessageResponseSchema(message=SuccessMessage.RESET_PASSWORD_EMAIL_SENT)

    @get("/verify-email-reset-password/{token}")
    def verify_email_reset_password(self, token: str):
        user = self.service.verify_email_reset_password(token=token)
        new_token = get_key(user=user)
        frontend_url = os.environ.get("FRONTEND_RESET_PASSWORD_URL")
        if not frontend_url:
            raise FrontendURLNotConfigured
        encoded_token = quote(new_token.token)
        return redirect(f"{frontend_url}?token={encoded_token}")

    @put("/save-password", response=MessageResponseSchema)
    def save_password(self, payload: SavePasswordSchema):
        self.service.save_password(
            token=payload.token, new_password=payload.new_password
        )
        return MessageResponseSchema(message=SuccessMessage.PASSWORD_RESET_SUCCESS)
