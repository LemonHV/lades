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


class BrandDoesNotExists(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "BRAND_DOES_NOT_EXISTS"
    message = "Thương hiệu không tồn tại."


class ProductImageDoesNotExists(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "PRODUCT_IMAGE_DOES_NOT_EXISTS"
    message = "Ảnh sản phẩm không tồn tại."


class ProductOutOfStock(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "PRODUCT_OUT_OF_STOCK"
    message = "Sản phẩm không còn đủ số lượng trong kho."


class QuantityQRCodeInvalid(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "QUANTITY_QR_CODE_INVALID"
    message = "Số lượng mã QR không hợp lệ"

class VerifyCodeDoesNotExists(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "VERIFY_CODE_DOES_NOT_EXISTS"
    message = "Mã QR xác thực không tồn tại."