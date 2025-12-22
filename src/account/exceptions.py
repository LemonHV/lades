from http import HTTPStatus

from router.exception import APIException


class EmailAlreadyExists(APIException):
    error_code = HTTPStatus.CONFLICT
    message_code = "EMAIL_ALREADY_EXISTS"
    message = "Email đã tồn tại"


class EmailNotExists(APIException):
    error_code = HTTPStatus.CONFLICT
    message_code = "EMAIL_NOT_EXISTS"
    message = "Email không tồn tại"


class EmailRequired(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "EMAIL_REQUIRED"
    message = "Email không được để trống"


class PasswordRequired(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "PASSWORD_REQUIRED"
    message = "Password không được để trống"


class BackendURLNotConfigured(APIException):
    error_code = HTTPStatus.INTERNAL_SERVER_ERROR
    message_code = "BACKEND_URL_NOT_CONFIGURED"
    message = "BACKEND_URL chưa được cấu hình trong environment"


class InvalidOrExpiredToken(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "INVALID_OR_EXPIRED_TOKEN"
    message = "Invalid or expired token"


class FrontendURLNotConfigured(APIException):
    error_code = HTTPStatus.INTERNAL_SERVER_ERROR
    message_code = "FRONTEND_URL_NOT_CONFIGURED"
    message = "Frontend redirect URL is not configured"


class UserNotActive(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "USER_NOT_ACTIVE"
    message = "Tài khoản chưa được xác thực email"


class EmailOrPasswordInvalid(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "INVALID_EMAIL_OR_PASSWORD"
    message = "Invalid email or password"


class GoogleClientIDNotConfigured(APIException):
    error_code = HTTPStatus.INTERNAL_SERVER_ERROR
    message_code = "GOOGLE_CLIENT_ID_NOT_CONFIGURED"
    message = "Google Client ID is not configured"


class OldPasswordInvalid(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "OLD_PASSWORD_INVALID"
    message = "Mật khẩu cũ không đúng"
