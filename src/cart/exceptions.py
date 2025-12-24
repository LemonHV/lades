from http import HTTPStatus

from router.exception import APIException


class CartItemDoesNotExists(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "CART_ITEM_DOES_NOT_EXISTS"
    message = "Sản phẩm trong tồn tại trong giỏ hàng"


class CartDoesNotExists(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "CART_DOES_NOT_EXISTS"
    message = "Giỏ hàng không tồn tại"
