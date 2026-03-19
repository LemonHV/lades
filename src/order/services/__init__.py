from order.orm.order import OrderORM
from order.orm.payment import PaymentORM
from order.models import Order
from order.schemas import (
    OrderRequestSchema,
    DiscountRequestSchema,
    UpdateOrderStatusSchema,
)
from order.exceptions import OrderDoesNotExists
from account.models import User
from uuid import UUID
from datetime import datetime

from django.utils import timezone
from order.utils import OrderStatus, PaymentStatus
import re

class OrderService:
    def __init__(self):
        self.orm = OrderORM()

    def create_order(self, user: User, payload: OrderRequestSchema):
        return self.orm.create_order(user=user, payload=payload)

    def handle_sepay_webhook(self, payload: dict):
        self.orm.handle_sepay_webhook(payload=payload)

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
    def _get_payload_value(payload, key: str, default=None):
        if isinstance(payload, dict):
            return payload.get(key, default)
        return getattr(payload, key, default)

    @staticmethod
    def _payload_to_dict(payload) -> dict:
        if isinstance(payload, dict):
            return payload
        if hasattr(payload, "model_dump"):
            return payload.model_dump()
        if hasattr(payload, "dict"):
            return payload.dict()
        return {}

    @staticmethod
    def _normalize_text(text: str | None) -> str:
        if not text:
            return ""
        return " ".join(text.strip().upper().split())

    @staticmethod
    def _extract_order_code(content: str) -> str | None:
        normalized = PaymentService._normalize_text(content)
        if not normalized:
            return None

        # Ví dụ bắt ORDER001, DH001, ABC123...
        match = re.search(r"\b[A-Z]{1,10}\d{2,20}\b", normalized)
        if match:
            return match.group(0)

        parts = normalized.split()
        return parts[-1] if parts else None

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

    def handle_sepay_webhook(self, payload):
        raw_payload = self._payload_to_dict(payload)

        transfer_type = str(
            self._get_payload_value(payload, "transferType", "")
        ).lower()
        transaction_id = self._get_payload_value(payload, "id")
        content = self._get_payload_value(payload, "content", "")
        transfer_amount = self._get_payload_value(payload, "transferAmount", 0)
        transaction_date = self._get_payload_value(payload, "transactionDate")
        reference_code = self._get_payload_value(payload, "referenceCode")

        # 1. Chỉ xử lý tiền vào
        if transfer_type != "in":
            return {
                "success": True,
                "message": "Ignored non-incoming transaction",
            }

        # 2. Chống duplicate theo transaction id
        existed_payment = self.orm.get_payment_by_sepay_transaction_id(transaction_id)
        if existed_payment:
            return {
                "success": True,
                "message": "Transaction already processed",
            }

        # 3. Tách mã đơn
        order_code = self._extract_order_code(content)
        if not order_code:
            return {
                "success": True,
                "message": "Cannot extract order code, ignored",
            }

        # 4. Tìm order theo code
        order = self.orm.get_order_by_code(order_code)
        if not order:
            return {
                "success": True,
                "message": f"Order {order_code} not found, ignored",
            }

        # 5. Tìm payment
        payment = self.orm.get_payment_by_order(order)
        if not payment:
            return {
                "success": True,
                "message": f"Payment for order {order_code} not found, ignored",
            }

        # 6. Nếu đã success rồi thì bỏ qua, không trả lỗi
        if (
            payment.status == PaymentStatus.SUCCESS
            or order.status == OrderStatus.PROCESSING
        ):
            return {
                "success": True,
                "message": "Payment already processed",
            }

        # 7. Đối chiếu số tiền
        try:
            if int(payment.amount) != int(transfer_amount):
                return {
                    "success": False,
                    "message": "Amount mismatch",
                }
        except Exception:
            return {
                "success": False,
                "message": "Invalid amount",
            }

        # 8. Parse thời gian
        paid_at = self._parse_transaction_datetime(transaction_date)

        # 9. Update payment + order
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
