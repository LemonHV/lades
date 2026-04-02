import re
from datetime import datetime
from uuid import UUID

from django.utils import timezone

from account.models import User
from order.exceptions import OrderDoesNotExists
from order.models import Order
from order.orm.order import OrderORM
from order.orm.payment import PaymentORM
from order.schemas import (
    DiscountRequestSchema,
    OrderRequestSchema,
    UpdateOrderStatusSchema,
)
from order.utils import OrderStatus, PaymentStatus


class OrderService:
    def __init__(self):
        self.orm = OrderORM()

    def create_order(self, user: User, payload: OrderRequestSchema):
        return self.orm.create_order(user=user, payload=payload)

    def update_order_status(self, uid: UUID, payload: UpdateOrderStatusSchema):
        try:
            order = Order.objects.get(uid=uid)
        except Order.DoesNotExist:
            raise OrderDoesNotExists
        self.orm.update_order_status(order=order, payload=payload)

    def get_order_by_uid(self, uid: UUID):
        return self.orm.get_order_by_uid(uid=uid)

    def get_user_orders(self, user: User):
        return self.orm.get_user_orders(user=user)

    def get_admin_orders(self):
        return self.orm.get_admin_orders()

    def print_order(self, uid: UUID):
        try:
            order = Order.objects.get(uid=uid)
        except Order.DoesNotExist:
            raise OrderDoesNotExists
        return self.orm.print_order(order=order)

    def create_discount(self, payload: DiscountRequestSchema):
        return self.orm.create_discount(payload=payload)

    def get_discount_by_uid(self, uid: UUID):
        return self.orm.get_discount_by_uid(uid=uid)

    def get_discounts(self):
        return self.orm.get_discounts()

    def update_discount(self, uid: UUID, payload: DiscountRequestSchema):
        discount = self.orm.get_discount_by_uid(uid=uid)
        return self.orm.update_discount(discount=discount, payload=payload)


class PaymentService:
    def __init__(self):
        self.orm = PaymentORM()

    @staticmethod
    def _normalize_text(text: str | None) -> str:
        if not text:
            return ""
        return " ".join(text.strip().upper().split())

    @staticmethod
    def _extract_order_code(payload) -> str | None:
        prefix_code = str(getattr(payload, "code", "") or "").strip().upper()
        content = str(getattr(payload, "content", "") or "").strip().upper()

        if not content:
            return None

        # Nếu content bắt đầu bằng prefix cố định của SePay
        # thì phần phía sau mới là mã đơn thật
        if prefix_code and content.startswith(prefix_code):
            real_order_code = content[len(prefix_code) :].strip()
            return real_order_code or None

        # fallback nếu không có prefix
        return content

    @staticmethod
    def _parse_transaction_datetime(value: str | None):
        if not value:
            return timezone.now()

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                return timezone.make_aware(dt, timezone.get_current_timezone())
            except Exception:
                pass

        return timezone.now()

    @staticmethod
    def _payload_to_dict(payload):
        if hasattr(payload, "model_dump"):
            return payload.model_dump()
        if hasattr(payload, "dict"):
            return payload.dict()
        return dict(payload)

    def handle_sepay_webhook(self, payload):
        raw_payload = self._payload_to_dict(payload)

        transfer_type = str(getattr(payload, "transferType", "") or "").lower()
        transaction_id = getattr(payload, "id", None)
        transfer_amount = getattr(payload, "transferAmount", 0)
        transaction_date = getattr(payload, "transactionDate", None)
        reference_code = getattr(payload, "referenceCode", None)

        if transfer_type != "in":
            return {
                "success": True,
                "message": "Ignore outgoing transaction",
            }

        existed_payment = self.orm.get_payment_by_sepay_transaction_id(transaction_id)
        if existed_payment:
            return {
                "success": True,
                "message": "Transaction already processed",
            }

        order_code = self._extract_order_code(payload)
        if not order_code:
            return {
                "success": True,
                "message": "Cannot extract order code",
            }

        order = self.orm.get_order_by_code(order_code)
        if not order:
            return {
                "success": True,
                "message": f"Order {order_code} not found",
            }

        payment = self.orm.get_payment_by_order(order)
        if not payment:
            return {
                "success": True,
                "message": f"Payment for order {order_code} not found",
            }

        if payment.status == PaymentStatus.SUCCESS:
            return {
                "success": True,
                "message": "Payment already paid",
            }

        if int(payment.amount) != int(transfer_amount):
            return {
                "success": False,
                "message": f"Amount mismatch: db={payment.amount}, webhook={transfer_amount}",
            }

        paid_at = self._parse_transaction_datetime(transaction_date)

        self.orm.mark_payment_and_order_paid(
            payment=payment,
            order=order,
            sepay_transaction_id=transaction_id,
            sepay_reference_code=reference_code,
            paid_at=paid_at,
            raw_payload=raw_payload,
        )

        return {
            "success": True,
            "message": "Payment confirmed successfully",
        }

    def confirm_payment_success(self, uid: UUID, user):
        return self.orm.confirm_payment_success(uid=uid, user=user)
