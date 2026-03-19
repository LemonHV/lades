from django.db import transaction
from uuid import UUID
from order.models import Order, Payment
from order.utils import PaymentStatus, OrderStatus
from order.exceptions import PaymentDoesNotExists


class PaymentORM:
    @staticmethod
    def get_payment_by_sepay_transaction_id(sepay_transaction_id: int):
        return Payment.objects.filter(sepay_transaction_id=sepay_transaction_id).first()

    @staticmethod
    def get_pending_order_by_code(order_code: str):
        return Order.objects.filter(
            code=order_code,
            status="PENDING",
        ).first()

    @staticmethod
    def get_payment_by_order(order: Order):
        return Payment.objects.filter(order=order).first()

    @staticmethod
    def mark_payment_paid(
        payment: Payment,
        sepay_transaction_id: int,
        sepay_reference_code: str,
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
        order.status = OrderStatus.PROCESSING
        order.save(update_fields=["status"])
        return order

    @staticmethod
    def mark_payment_and_order_paid(
        payment: Payment,
        order: Order,
        sepay_transaction_id: int,
        sepay_reference_code: str,
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

    def confirm_payment_success(uid: UUID):
        try:
            payment = Payment.objects.get(uid=uid)
        except Payment.DoesNotExist:
            raise PaymentDoesNotExists
        if payment.status == "SUCCESS":
            return {"status": "SUCCESS", "message": "Thanh toán thành công"}

        return {"status": "PENDING", "message": "Chưa thanh toán"}
