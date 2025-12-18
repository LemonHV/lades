from http import HTTPStatus

from .exception import APIException


class ProductDoesNotExist(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "PRODUCT_DOES_NOT_EXIST"
    message = "The requested product does not exist"
