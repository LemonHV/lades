from uuid import UUID
from product.models import Product, VerifyCode, VerifierLocation
from attachment.models import Attachment
from product.schemas import ProductInfoSchema
from django.db.models import Prefetch


class VerifyCodeORM:
    @staticmethod
    def create_verify_code(product: Product, code: str, attachment: Attachment):
        return VerifyCode.objects.create(
            product=product, code=code, attachment=attachment
        )

    @staticmethod
    def get_verify_code_by_uid(uid: UUID):
        return VerifyCode.objects.filter(uid=uid).first()

    @staticmethod
    def get_verify_code_by_code(code: str):
        return (
            VerifyCode.objects.select_for_update()
            .select_related("product")
            .filter(code=code)
            .first()
        )

    @staticmethod
    def get_product_info(uid: UUID) -> ProductInfoSchema:
        return Product.objects.filter(uid=uid).first()

    @staticmethod
    def create_verifier_location(**verifier_location_info):
        return VerifierLocation.objects.create(**verifier_location_info)

    @staticmethod
    def get_verifier_location_by_code(code: str):
        return VerifierLocation.objects.select_related("verify_code").filter(
            verify_code__code=code
        )

    @staticmethod
    def increase_scan_count(verify_code: VerifyCode):
        verify_code.scan_count += 1
        verify_code.save(update_fields=["scan_count"])
