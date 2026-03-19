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
from ninja.errors import HttpError


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
    def _normalize_text(text: str | None) -> str:
        if not text:
            return ""
        return " ".join(text.strip().upper().split())

    @staticmethod
    def _extract_order_code(content: str) -> str | None:
        normalized = PaymentService._normalize_text(content)
        if not normalized:
            return None

        prefix = "TKPMTV "
        if normalized.startswith(prefix):
            code = normalized[len(prefix) :].strip()
            return code or None

        parts = normalized.split(" ")
        return parts[-1] if parts else None

    @staticmethod
    def _parse_transaction_datetime(value: str | None):
        if not value:
            return timezone.now()

        try:
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return timezone.make_aware(dt, timezone.get_current_timezone())
        except Exception:
            return timezone.now()

    def handle_sepay_webhook(self, payload):
        # 1. Chỉ xử lý giao dịch tiền vào
        if payload.transferType.lower() != "in":
            return {
                "success": True,
                "message": "Ignore outgoing transaction",
            }

        # 2. Chống xử lý trùng
        existed_payment = self.orm.get_payment_by_sepay_transaction_id(payload.id)
        if existed_payment:
            return {
                "success": True,
                "message": "Transaction already processed",
            }

        # 3. Tách mã đơn từ nội dung chuyển khoản
        order_code = self._extract_order_code(payload.content)
        if not order_code:
            raise HttpError(400, "Cannot extract order code")

        # 4. Tìm order pending
        order = self.orm.get_pending_order_by_code(order_code)
        if not order:
            raise HttpError(404, "Order not found or already processed")

        # 5. Tìm payment của order
        payment = self.orm.get_payment_by_order(order)
        if not payment:
            raise HttpError(404, "Payment not found")

        # 6. Nếu payment đã paid thì bỏ qua
        if payment.status == "PAID":
            return {
                "success": True,
                "message": "Payment already paid",
            }

        # 7. Đối chiếu số tiền
        if int(payment.amount) != int(payload.transferAmount):
            raise HttpError(409, "Amount mismatch")

        # 8. Parse thời gian giao dịch
        paid_at = self._parse_transaction_datetime(payload.transactionDate)

        # 9. Cập nhật payment + order
        self.orm.mark_payment_and_order_paid(
            payment=payment,
            order=order,
            sepay_transaction_id=payload.id,
            sepay_reference_code=payload.referenceCode,
            paid_at=paid_at,
            raw_payload=payload.dict(),
        )

        return {
            "success": True,
            "message": "Payment confirmed successfully",
        }

    def confirm_payment_success(self, uid: UUID):
        return self.orm.confirm_payment_success(uid=uid)
