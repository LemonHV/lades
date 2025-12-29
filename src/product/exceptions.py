from http import HTTPStatus

from router.exception import APIException


class ProductFileRequired(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "PRODUCT_FILE_REQUIRED"
    message = "File sản phẩm là bắt buộc."


class ProductDoesNotExists(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "PRODUCT_DOES_NOT_EXISTS"
    message = "Sản phẩm không tồn tại."

class ProductOutOfStock(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "PRODUCT_OUT_OF_STOCK"
    message = "Sản phẩm không còn đủ số lượng trong kho."
