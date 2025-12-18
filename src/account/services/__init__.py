import os

import requests

from account.models import User
from account.orm.account import AccountORM
from exceptions.auth import (
    InvalidOrExpiredToken,
    UserNameAlreadyExists,
    UsernameOrPasswordInvalid,
)


class AccountService:
    def __init__(self):
        self.orm = AccountORM()

    def register(self, identifier: str, password: str) -> User:
        if not identifier or not password:
            raise UsernameOrPasswordInvalid
        user = self.orm.register(identifier=identifier, password=password)
        if user is None:
            raise UserNameAlreadyExists
        return user

    def login_with_credential(self, identifier: str, password: str) -> str | None:
        if not identifier or not password:
            raise UsernameOrPasswordInvalid
        token = self.orm.login_with_credential(identifier=identifier, password=password)
        if token is None:
            raise UsernameOrPasswordInvalid
        return token

    def logout(self, token: str):
        if not token:
            return False
        return self.orm.logout(token=token)

    @staticmethod
    def verify_id_token(id_token: str) -> dict:
        resp = requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
            timeout=5,
        )

        if resp.status_code != 200:
            raise InvalidOrExpiredToken

        data = resp.json()

        if data.get("aud") != os.environ.get("GOOGLE_CLIENT_ID"):
            raise InvalidOrExpiredToken

        return data

    def login_with_google(self, id_token: str) -> str:
        if not id_token:
            raise InvalidOrExpiredToken

        google_data = self.verify_id_token(id_token)
        return self.orm.login_with_google(
            google_id=google_data["sub"],
            email=google_data.get("email"),
            name=google_data.get("name"),
        )
