import os
import secrets
from uuid import UUID
from account.exceptions import BackendURLNotConfigured
from product.exceptions import (
    ProductDoesNotExists,
    QuantityQRCodeInvalid,
    VerifyCodeDoesNotExists,
)
from product.orm.product import ProductORM
from product.orm.verify_code import VerifyCodeORM
from product.utils import generate_qr_image, get_ip_location
from attachment.services import AttachmentService
from attachment.models import AttachmentType
from product.schemas import VerifierLocationSchema


class VerifyCodeService:
    def __init__(self):
        self.orm = VerifyCodeORM()
        self.product_orm = ProductORM()
        self.attachment_service = AttachmentService()

    def generate_verify_qr_code(self, uid: UUID):
        product = self.product_orm.get_product_by_uid(uid=uid)
        if not product:
            raise ProductDoesNotExists

        code = secrets.token_urlsafe(32)

        backend_url = os.environ.get("BACKEND_URL")
        if not backend_url:
            raise BackendURLNotConfigured

        link = f"{backend_url}/api/verifycodes/verify-qrcode?code={code}"
        buffer = generate_qr_image(link=link)

        attachment = self.attachment_service.upload_attachment(
            file=buffer,
            folder="qr_codes/",
            public_id=f"verify_{code}",
            type=AttachmentType.VERIFYCODE,
        )

        return self.orm.create_verify_code(
            product=product, code=code, attachment=attachment
        )

    def generate_multiple_verify_qr_codes(self, uid: UUID, quantity: int):
        if quantity <= 0:
            raise QuantityQRCodeInvalid
        verify_codes = []

        for _ in range(quantity):
            verify_code = self.generate_verify_qr_code(uid=uid)
            verify_codes.append(verify_code)

        return verify_codes

    def create_verifier_location(self, payload: VerifierLocationSchema):
        verifier_location_info = payload.dict()
        verify_code_uid = verifier_location_info.pop("verify_code_uid")
        verify_code = self.orm.get_verify_code_by_uid(uid=verify_code_uid)
        if not verify_code:
            return VerifyCodeDoesNotExists
        return self.orm.create_verifier_location(
            verify_code=verify_code, **verifier_location_info
        )

    def verify_qrcode(self, code: str, client_ip: str):
        verify_code = self.orm.get_verify_code_by_code(code=code)
        if not verify_code:
            return {
                "status": "FAKE",
                "message": "Mã QR không tồn tại. Có thể là hàng giả.",
                "product": None,
                "scan_count": 0,
            }

        verifier_location_info = get_ip_location(client_ip) or {}
        self.orm.create_verifier_location(
            verify_code_uid=verify_code.uid,
            **verifier_location_info,
        )

        product_info = self.orm.get_product_info(uid=verify_code.product.uid)

        if verify_code.scan_count >= verify_code.max_scan:
            return {
                "status": "FAKE",
                "message": "Mã QR đã bị quét vượt số lần cho phép. Có dấu hiệu hàng giả.",
                "product": None,
                "scan_count": verify_code.scan_count,
            }

        verify_code = self.orm.increase_scan_count(verify_code=verify_code)

        if verify_code.scan_count > 1:
            return {
                "status": "SCANNED",
                "message": "Mã QR đã được quét trước đó.",
                "product": product_info,
                "scan_count": verify_code.scan_count,
            }

        return {
            "status": "AUTHENTIC",
            "message": "Sản phẩm chính hãng.",
            "product": product_info,
            "scan_count": verify_code.scan_count,
        }
