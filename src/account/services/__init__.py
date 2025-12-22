import os

import requests

from account.exceptions import (
    EmailAlreadyExists,
    EmailOrPasswordInvalid,
    EmailRequired,
    GoogleClientIDNotConfigured,
    InvalidOrExpiredToken,
    OldPasswordInvalid,
    PasswordRequired,
    UserNotActive,
)
from account.models import User
from account.orm.account import AccountORM


class AccountService:
    def __init__(self):
        self.orm = AccountORM()

    def register(self, email: str, password: str) -> None:
        if not email:
            raise EmailRequired
        if not password:
            raise PasswordRequired
        if User.objects.filter(email=email).exists():
            raise EmailAlreadyExists
        self.orm.register(email=email, password=password)

    def verify_email_register(self, token: str) -> None:
        if not token:
            raise InvalidOrExpiredToken
        self.orm.verify_email_register(token=token)

    def login_with_credential(self, email: str, password: str) -> str:
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise EmailOrPasswordInvalid
        if not user.check_password(password):
            raise EmailOrPasswordInvalid

        if not user.is_active:
            raise UserNotActive
        return self.orm.login_with_credential(user=user)

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

    def login_with_google(self, id_token: str) -> str:
        if not id_token:
            raise InvalidOrExpiredToken

        google_data = self.verify_id_token(id_token)

        google_id = google_data.get("sub")
        email = google_data.get("email")
        name = google_data.get("name", "")

        if not google_id or not email:
            raise InvalidOrExpiredToken

        return self.orm.login_with_google(
            google_id=google_id,
            email=email,
            name=name,
        )

    def logout(self, token: str) -> None:
        print(token)
        if not token:
            raise InvalidOrExpiredToken

        self.orm.logout(token=token)

    def change_password(self, user: User, old_password: str, new_password: str):
        if not user.check_password(old_password):
            raise OldPasswordInvalid
        self.orm.change_password(user=user, new_password=new_password)

    def reset_password(self, email: str):
        if not email:
            raise EmailRequired
        self.orm.reset_password(email=email)

    def verify_email_reset_password(self, token: str):
        if not token:
            raise InvalidOrExpiredToken
        return self.orm.verify_email_reset_password(token=token)

    def save_password(self, token: str, new_password: str):
        if not token:
            raise InvalidOrExpiredToken
        if not new_password:
            raise PasswordRequired
        self.orm.save_password(token=token, new_password=new_password)
