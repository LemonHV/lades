from http import HTTPStatus

from router.exception import APIException


class UploadAttachmentFail(APIException):
    error_code = HTTPStatus.INTERNAL_SERVER_ERROR
    message_code = "ATTACHMENT_UPLOAD_FAIL"
    message = "Tải file thất bại"


class AttachmentNotExists(APIException):
    error_code = HTTPStatus.CONFLICT
    message_code = "ATTACHMENT_NOT_EXISTS"
    message = "Attachment không tồn tại"
