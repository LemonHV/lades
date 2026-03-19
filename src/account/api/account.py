import os
from urllib.parse import quote

from django.shortcuts import redirect

from account.exceptions import FrontendURLNotConfigured
from account.schemas.account import (
    ChangePasswordSchema,
    ForgotPasswordSchema,
    GoogleLoginSchema,
    LoginResponseSchema,
    LoginSchema,
    MessageResponseSchema,
    ResetPasswordConfirmSchema,
    UpdateUserInfoSchema,
    UserInfoSchema,
)
from account.services import AccountService
from account.utils import SuccessMessage, get_key
from router.authenticate import AuthBear
from router.controller import Controller, api, get, post, put
from router.types import AuthenticatedRequest


@api(prefix_or_class="accounts", tags=["Account"], auth=None)
class AccountAPI(Controller):
    def __init__(self, service: AccountService):
        self.service = service

    @staticmethod
    def _get_frontend_url(env_key: str) -> str:
        frontend_url = os.environ.get(env_key)
        if not frontend_url:
            raise FrontendURLNotConfigured
        return frontend_url.rstrip("/")

    @post("/register", response=MessageResponseSchema)
    def register(self, payload: LoginSchema):
        self.service.register(email=payload.email, password=payload.password)
        return MessageResponseSchema(message=SuccessMessage.REGISTER)

    @get("/verify-email-register/{token}")
    def verify_register_email(self, token: str):
        self.service.verify_register_email(token=token)
        frontend_url = self._get_frontend_url("FRONTEND_REGISTER_URL")
        return redirect(frontend_url)

    @post("/login-credential", response=LoginResponseSchema)
    def login_with_credential(self, payload: LoginSchema):
        return self.service.login_with_credential(
            email=payload.email,
            password=payload.password,
        )

    @post("/login-google", response=LoginResponseSchema)
    def login_with_google(self, payload: GoogleLoginSchema):
        return self.service.login_with_google(id_token=payload.id_token)

    @put("/logout", auth=AuthBear(), response=MessageResponseSchema)
    def logout(self, request: AuthenticatedRequest):
        self.service.logout(token=request.token.token)
        return MessageResponseSchema(message=SuccessMessage.LOGOUT)

    @put("/change-password", auth=AuthBear(), response=MessageResponseSchema)
    def change_password(
        self,
        request: AuthenticatedRequest,
        payload: ChangePasswordSchema,
    ):
        self.service.change_password(
            user=request.user,
            old_password=payload.old_password,
            new_password=payload.new_password,
        )
        return MessageResponseSchema(message=SuccessMessage.PASSWORD_CHANGED)

    @post("/reset-password", response=MessageResponseSchema)
    def reset_password(self, payload: ForgotPasswordSchema):
        self.service.reset_password(email=payload.email)
        return MessageResponseSchema(message=SuccessMessage.RESET_PASSWORD_EMAIL_SENT)

    @get("/verify-email-reset-password/{token}")
    def verify_email_reset_password(self, token: str):
        user = self.service.verify_email_reset_password(token=token)

        new_token = get_key(user=user, key_type="reset_password")
        frontend_url = self._get_frontend_url("FRONTEND_RESET_PASSWORD_URL")
        encoded_token = quote(new_token.token)

        return redirect(f"{frontend_url}?token={encoded_token}")

    @put("/save-password", response=MessageResponseSchema)
    def save_password(self, payload: ResetPasswordConfirmSchema):
        self.service.save_password(
            token=payload.token,
            new_password=payload.new_password,
        )
        return MessageResponseSchema(message=SuccessMessage.PASSWORD_RESET_SUCCESS)

    @get("/me", response=UserInfoSchema, auth=AuthBear())
    def get_info(self, request: AuthenticatedRequest):
        return request.user

    @put("/me", response=UserInfoSchema, auth=AuthBear())
    def update_info(
        self,
        request: AuthenticatedRequest,
        payload: UpdateUserInfoSchema,
    ):
        return self.service.update_info(user=request.user, payload=payload)
