from uuid import UUID

from django.db import transaction

from order.exceptions import PaymentDoesNotExists
from order.models import Order, Payment, OrderItem
from product.models import ProductImage
from django.db.models import Prefetch
from product.models import Product
from product.exceptions import ProductDoesNotExists, ProductOutOfStock
from order.exceptions import OrderDoesNotExists
from order.utils import OrderStatus, PaymentStatus
from order.utils import send_order_confirmation_email


class PaymentORM:
    @staticmethod
    def get_payment_by_sepay_transaction_id(sepay_transaction_id: int | None):
        if not sepay_transaction_id:
            return None
        return Payment.objects.filter(sepay_transaction_id=sepay_transaction_id).first()

    @staticmethod
    def get_order_by_code(order_code: str):
        try:
            return (
                Order.objects.select_related("user")
                .prefetch_related(
                    Prefetch(
                        "items",
                        queryset=OrderItem.objects.select_related(
                            "product"
                        ).prefetch_related(
                            Prefetch(
                                "product__product_images",
                                queryset=ProductImage.objects.select_related(
                                    "attachment"
                                ),
                                to_attr="images",
                            )
                        ),
                        to_attr="order_items",
                    )
                )
                .get(code=order_code)
            )
        except Order.DoesNotExist:
            raise OrderDoesNotExists

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
        payment.status = PaymentStatus.PAID
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
    @transaction.atomic
    def mark_order_confirmed(order: Order):
        order = (
            Order.objects.select_for_update()
            .prefetch_related("items__product")
            .get(uid=order.uid)
        )

        if order.status != OrderStatus.PENDING:
            return order

        items = list(order.items.all())
        product_uids = [item.product.uid for item in items]

        products = Product.objects.select_for_update().in_bulk(
            product_uids,
            field_name="uid",
        )

        for item in items:
            product = products.get(item.product.uid)
            if not product:
                raise ProductDoesNotExists

            if item.quantity <= 0:
                raise ProductOutOfStock

            if item.quantity > product.quantity_in_stock:
                raise ProductOutOfStock

        for item in items:
            product = products[item.product.uid]
            product.quantity_in_stock -= item.quantity
            product.save(update_fields=["quantity_in_stock"])

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
            send_order_confirmation_email(order=order, email=order.user.email)
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

        if payment.status == PaymentStatus.PAID:
            return {
                "status": "PAID",
                "message": "Đã thanh toán thành công",
            }

        if payment.status == PaymentStatus.UNPAID:
            return {
                "status": "UNPAID",
                "message": "Đơn hàng chưa được thanh toán",
            }

        return {
            "status": "PENDING",
            "message": "Chưa thanh toán",
        }
