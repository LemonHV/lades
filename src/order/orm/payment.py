from uuid import UUID

from django.db import transaction

from order.exceptions import PaymentDoesNotExists
from order.models import Order, Payment
from order.utils import OrderStatus, PaymentStatus


class PaymentORM:
    @staticmethod
    def get_payment_by_sepay_transaction_id(sepay_transaction_id: int | None):
        if not sepay_transaction_id:
            return None
        return Payment.objects.filter(sepay_transaction_id=sepay_transaction_id).first()

    @staticmethod
    def get_order_by_code(order_code: str):
        return Order.objects.filter(code=order_code).first()

    @staticmethod
    def get_payment_by_order(order: Order):
        return Payment.objects.filter(order=order).first()

    @staticmethod
    def mark_payment_paid(
        payment: Payment,
        sepay_transaction_id: int,
        sepay_reference_code: str | None,
        paid_at,
        raw_payload: dict,
    ):
        payment.status = PaymentStatus.SUCCESS
        payment.sepay_transaction_id = sepay_transaction_id
        payment.sepay_reference_code = sepay_reference_code
        payment.paid_at = paid_at
        payment.raw_payload = raw_payload

        update_fields = [
            "status",
            "sepay_transaction_id",
            "sepay_reference_code",
            "paid_at",
            "raw_payload",
        ]

        if hasattr(payment, "updated_at"):
            update_fields.append("updated_at")

        payment.save(update_fields=update_fields)
        return payment

    @staticmethod
    def mark_order_confirmed(order: Order):
        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.PROCESSING
            order.save(update_fields=["status"])
        return order

    @staticmethod
    def mark_payment_and_order_paid(
        payment: Payment,
        order: Order,
        sepay_transaction_id: int,
        sepay_reference_code: str | None,
        paid_at,
        raw_payload: dict,
    ):
        with transaction.atomic():
            PaymentORM.mark_payment_paid(
                payment=payment,
                sepay_transaction_id=sepay_transaction_id,
                sepay_reference_code=sepay_reference_code,
                paid_at=paid_at,
                raw_payload=raw_payload,
            )
            PaymentORM.mark_order_confirmed(order=order)

        return payment, order

    @staticmethod
    def confirm_payment_success(uid: UUID, user):
        try:
            payment = Payment.objects.select_related("order").get(uid=uid)
        except Payment.DoesNotExist:
            raise PaymentDoesNotExists

        if payment.order.user != user:
            raise PermissionError("Bạn không có quyền truy cập payment này")

        if payment.status == PaymentStatus.SUCCESS:
            return {
                "status": "SUCCESS",
                "message": "Thanh toán thành công",
            }

        if payment.status == PaymentStatus.FAILED:
            return {
                "status": "FAILED",
                "message": "Thanh toán thất bại",
            }

        return {
            "status": "PENDING",
            "message": "Chưa thanh toán",
        }
