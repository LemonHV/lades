from http import HTTPStatus

from router.exception import APIException


class DiscountDoesNotExists(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "DISCOUNT_DOES_NOT_EXISTS"
    message = "Mã giảm giá không tồn tại"


class ShippingInfoDoesNotExists(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "SHIPPING_INFO_DOES_NOT_EXISTS"
    message = "Thông tin giao hàng không tồn tại"


class OrderDoesNotExists(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "ORDER_DOES_NOT_EXISTS"
    message = "Đơn hàng không tồn tại"


class PaymentDoesNotExists(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "Payment_DOES_NOT_EXISTS"
    message = "Thanh toán không tồn tại"


class OrderCanNotRetryExists(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "ORDER_CAN_NOT_RETRY_EXISTS"
    message = "Không thể thanh toán lại"
