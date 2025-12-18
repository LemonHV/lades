from http import HTTPStatus

from .exception import APIException


class InvalidOrExpiredToken(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "INVALID_OR_EXPIRED_TOKEN"
    message = "Invalid or expired token"


class UserNameAlreadyExists(APIException):
    error_code = HTTPStatus.CONFLICT
    message_code = "USERNAME_ALREADY_EXISTS"
    message = "The username is already taken"


class UsernameOrPasswordInvalid(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "INVALID_USERNAME_OR_PASSWORD"
    message = "Invalid username or password"
