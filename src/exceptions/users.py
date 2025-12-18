from http import HTTPStatus

from .exception import APIException


class UserNotFound(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "USER_NOT_FOUND"
    message = "User not found"


class UsernameOrPasswordIncorrect(APIException):
    error_code = HTTPStatus.UNAUTHORIZED
    message_code = "USERNAME_OR_PASSWORD_INCORRECT"
    message = "Username or password incorrect"
