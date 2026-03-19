import os
import requests
from account.exceptions import (
    BackendURLNotConfigured,
    EmailAlreadyExists,
    EmailInvalid,
    EmailRequired,
    GoogleClientIDNotConfigured,
    InvalidOrExpiredToken,
    PasswordInvalid,
    PasswordRequired,
    UserNotActive,
    OldPasswordInvalid,
)
from account.models import User
from account.orm.account import AccountORM
from account.utils import get_key, send_verify_email
from account.schemas.account import LoginResponseSchema, UpdateUserInfoSchema


class AccountService:
    def __init__(self):
        self.orm = AccountORM()

    def register(self, email: str, password: str) -> None:
        if not email:
            raise EmailRequired
        if not password:
            raise PasswordRequired
        user = self.orm.get_user_by_email(email=email)
        if user:
            if user.is_active:
                raise EmailAlreadyExists
            else:
                user = self.orm.update_user_password(user=user, new_password=password)
        else:
            user = self.orm.create_user(email=email, password=password)
        token_object = get_key(user=user, key_type="register")
        backend_url = os.environ.get("BACKEND_URL")
        if not backend_url:
            raise BackendURLNotConfigured
        link = f"{backend_url}/api/accounts/verify-email-register/{token_object.token}"
        send_verify_email(link=link, email=user.email, verify_type="register")

    def verify_register_email(self, token: str) -> None:
        token_object = self.orm.get_valid_token(token=token, key_type="register")
        if not token_object:
            raise InvalidOrExpiredToken
        self.orm.activate_user(user=token_object.user)
        self.orm.blacklist_token(token_object=token_object)

    def login_with_credential(
        self,
        email: str,
        password: str,
    ) -> LoginResponseSchema:
        if not email:
            raise EmailRequired
        if not password:
            raise PasswordRequired
        user = self.orm.get_user_by_email(email=email)
        if not user:
            raise EmailInvalid

        if not user.check_password(password):
            raise PasswordInvalid

        if not user.is_active:
            raise UserNotActive

        return LoginResponseSchema(
            is_staff=user.is_staff,
            token=get_key(user=user, key_type="login").token,
        )

    @staticmethod
    def verify_id_token(id_token: str) -> dict:
        try:
            resp = requests.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token},
                timeout=5,
            )
        except requests.RequestException:
            raise InvalidOrExpiredToken

        if resp.status_code != 200:
            raise InvalidOrExpiredToken

        data = resp.json()

        google_client_id = os.environ.get("GOOGLE_CLIENT_ID")
        if not google_client_id:
            raise GoogleClientIDNotConfigured

        if data.get("aud") != google_client_id:
            raise InvalidOrExpiredToken

        return data

    def login_with_google(self, id_token: str) -> LoginResponseSchema:
        if not id_token:
            raise InvalidOrExpiredToken

        google_data = self.verify_id_token(id_token=id_token)

        google_id = google_data.get("sub")
        email = google_data.get("email")
        name = (google_data.get("name") or "").strip()

        if not google_id or not email:
            raise InvalidOrExpiredToken

        user = self.orm.get_user_by_google_id(google_id=google_id)
        if user:
            return LoginResponseSchema(
                is_staff=user.is_staff,
                token=get_key(user=user, key_type="login").token,
            )

        user = self.orm.get_user_by_email(email=email)
        if user:
            user = self.orm.update_user_info(
                user,
                google_id=google_id,
                is_active=True,
                name=name if name else user.name,
            )
            return LoginResponseSchema(
                is_staff=user.is_staff,
                token=get_key(user=user, key_type="login").token,
            )

        user = self.orm.create_user(
            email=email,
            password=None,
            is_active=True,
            google_id=google_id,
            name=name,
        )
        return LoginResponseSchema(
            is_staff=user.is_staff,
            token=get_key(user=user, key_type="login").token,
        )

    def logout(self, token: str) -> None:
        token_object = self.orm.get_valid_token(token=token, key_type="login")
        if not token_object:
            raise InvalidOrExpiredToken
        self.orm.blacklist_token(token_object=token_object)

    def change_password(self, user: User, old_password: str, new_password: str) -> None:
        if not old_password:
            raise PasswordRequired

        if not new_password:
            raise PasswordRequired

        if not user.check_password(old_password):
            raise OldPasswordInvalid
        self.orm.update_user_password(user=user, new_password=new_password)

    def reset_password(self, email: str) -> None:
        if not email:
            raise EmailRequired
        user = self.orm.get_user_by_email(email=email)
        if not user:
            return
        backend_url = os.environ.get("BACKEND_URL")
        if not backend_url:
            raise BackendURLNotConfigured

        token_object = get_key(user=user, key_type="reset_password")

        link = f"{backend_url}/api/accounts/verify-email-reset-password/{token_object.token}"

        send_verify_email(
            link=link,
            email=user.email,
            verify_type="reset_password",
        )

    def verify_email_reset_password(self, token: str) -> User:
        token_object = self.orm.get_valid_token(
            token=token,
            key_type="reset_password",
        )
        if not token_object:
            raise InvalidOrExpiredToken

        self.orm.blacklist_token(token_object=token_object)
        return token_object.user

    def save_password(self, token: str, new_password: str) -> None:
        if not token:
            raise InvalidOrExpiredToken
        if not new_password:
            raise PasswordRequired

        token_object = self.orm.get_valid_token(
            token=token,
            key_type="reset_password",
        )
        if not token_object:
            raise InvalidOrExpiredToken

        self.orm.update_user_password(
            user=token_object.user,
            new_password=new_password,
        )
        self.orm.blacklist_token(token_object=token_object)

    def update_info(self, user: User, payload: UpdateUserInfoSchema) -> User:
        data = payload.model_dump(exclude_unset=True)
        return self.orm.update_user_info(user=user, **data)
