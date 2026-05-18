import re
from uuid import UUID
from datetime import datetime, date, time
from django.utils import timezone

from account.models import User
from order.exceptions import OrderDoesNotExists, DiscountNotExistsOrExpired
from order.models import Order
from order.orm.order import OrderORM
from order.orm.payment import PaymentORM
from order.schemas import (
    DiscountRequestSchema,
    OrderRequestSchema,
    UpdateOrderStatusSchema,
    SePayWebhookSchema,
    SearchFilterSortSchema,
)
from order.utils import PaymentStatus


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

    def get_user_orders(self, user: User, payload: SearchFilterSortSchema):
        return self.orm.get_user_orders(user=user, payload=payload)

    def get_admin_orders(self, payload: SearchFilterSortSchema):
        return self.orm.get_admin_orders(payload=payload)

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

    def get_discount_by_code(self, code: str):
        discount = self.orm.get_discount_by_code(code=code)
        if not discount:
            raise DiscountNotExistsOrExpired
        return discount


class PaymentService:
    def __init__(self):
        self.orm = PaymentORM()

    @staticmethod
    def _parse_transaction_datetime(value):
        """
        Chuẩn hóa transactionDate từ webhook sang timezone-aware datetime
        """
        if not value:
            return timezone.now()

        if isinstance(value, datetime):
            if timezone.is_naive(value):
                return timezone.make_aware(value, timezone.get_current_timezone())
            return value

        if isinstance(value, date):
            dt = datetime.combine(value, time.min)
            return timezone.make_aware(dt, timezone.get_current_timezone())

        value = str(value).strip()

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                return timezone.make_aware(dt, timezone.get_current_timezone())
            except ValueError:
                continue

        return timezone.now()

    @staticmethod
    def _payload_to_dict(payload):
        """
        Convert webhook payload về dict để lưu raw data
        """
        if hasattr(payload, "model_dump"):
            return payload.model_dump()

        if hasattr(payload, "dict"):
            return payload.dict()

        return dict(payload)

    @staticmethod
    def _extract_order_code(content):
        """
        Format SePay:
        DH1029694AKLYJ2WAI36QUA76BAD

        Trong đó:
        DH102969 = prefix thanh toán
        4AKLYJ2WAI36QUA76BAD = mã đơn hàng
        """
        content = str(content or "").strip().upper()

        match = re.match(r"^DH\d{6}([A-Z0-9]+)$", content)

        if not match:
            return None

        return match.group(1)

    def handle_sepay_webhook(self, payload: SePayWebhookSchema):
        raw_payload = self._payload_to_dict(payload)

        # Chỉ xử lý tiền vào
        if str(payload.transferType).lower() != "in":
            return {
                "success": True,
                "message": "Ignore outgoing transaction",
            }

        # Chống webhook trùng
        existed_payment = self.orm.get_payment_by_sepay_transaction_id(payload.id)

        if existed_payment:
            return {
                "success": True,
                "message": "Transaction already processed",
            }

        # Parse mã đơn
        order_code = self._extract_order_code(payload.content)

        if not order_code:
            return {
                "success": True,
                "message": f"Cannot extract order code from content: {payload.content}",
            }

        # Tìm đơn hàng
        order = self.orm.get_order_by_code(order_code)

        if not order:
            return {
                "success": True,
                "message": f"Order {order_code} not found",
            }

        # Tìm payment
        payment = self.orm.get_payment_by_order(order)

        if not payment:
            return {
                "success": True,
                "message": f"Payment for order {order_code} not found",
            }

        # Đã thanh toán trước đó
        if payment.status == PaymentStatus.PAID:
            return {
                "success": True,
                "message": "Payment already paid",
            }

        # Check số tiền
        if int(payment.amount) != int(payload.transferAmount):
            return {
                "success": False,
                "message": (
                    f"Amount mismatch: "
                    f"db={payment.amount}, "
                    f"webhook={payload.transferAmount}"
                ),
            }

        # Parse ngày thanh toán
        paid_at = self._parse_transaction_datetime(payload.transactionDate)

        # Update DB
        self.orm.mark_payment_and_order_paid(
            payment=payment,
            order=order,
            sepay_transaction_id=payload.id,
            sepay_reference_code=payload.referenceCode,
            paid_at=paid_at,
            raw_payload=raw_payload,
        )

        return {
            "success": True,
            "message": "Payment confirmed successfully",
        }

    def confirm_payment_success(self, uid: UUID, user):
        return self.orm.confirm_payment_success(uid=uid, user=user)
