from uuid import UUID
from product.models import Product, ProductImage
from product.exceptions import ProductDoesNotExists, ProductOutOfStock
from order.utils import (
    generate_code,
    generate_order_bill,
    send_order_confirmation_email,
    generate_signature,
)
from order.schemas import (
    OrderRequestSchema,
    DiscountRequestSchema,
    UpdateOrderStatusSchema,
)
from order.models import Order, OrderItem, Discount, Payment
from django.utils.timezone import now
from django.db import transaction
from django.db.models import Prefetch
from cart.models import CartItem
from account.models import User, ShippingInfo
from order.exceptions import (
    ShippingInfoDoesNotExists,
    OrderDoesNotExists,
    DiscountDoesNotExists,
)
import os
import requests
from account.utils import SuccessMessage


class OrderORM:
    @staticmethod
    @transaction.atomic
    def create_order(user: User, payload: OrderRequestSchema):
        # ================================
        # 1. GET ITEMS
        # ================================
        if payload.source == "buy_now":
            buy_items = payload.order_items
            cart_items = None
        else:
            cart_items = (
                CartItem.objects.select_related("product")
                .select_for_update()
                .filter(cart__user=user, uid__in=payload.cart_item_uids)
            )
            buy_items = None

        # ================================
        # 2. SHIPPING INFO
        # ================================
        try:
            shipping_info = ShippingInfo.objects.get(id=payload.shipping_info_id)
        except ShippingInfo.DoesNotExist:
            raise ShippingInfoDoesNotExists

        # ================================
        # 3. CREATE ORDER
        # ================================
        order = Order.objects.create(
            code=generate_code(),
            order_date=now(),
            status="PENDING",
            shipping_fee=15000,
            discount_amount=0,
            total_amount=0,
            payment_method=payload.payment_method,
            note=payload.note,
            name=shipping_info.name,
            phone=shipping_info.phone,
            address=shipping_info.address,
            user=user,
        )

        # ================================
        # 4. CREATE ORDER ITEMS + HOLD STOCK
        # ================================
        items_total = 0

        if payload.source == "buy_now":
            products = Product.objects.select_for_update().in_bulk(
                [item.product_uid for item in buy_items],
                field_name="uid",
            )

            for item in buy_items:
                product = products.get(item.product_uid)
                if not product:
                    raise ProductDoesNotExists

                if item.quantity > product.quantity_in_stock:
                    raise ProductOutOfStock

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=product.sale_price,
                    quantity=item.quantity,
                )

                product.quantity_in_stock -= item.quantity
                product.save(update_fields=["quantity_in_stock"])

                items_total += product.sale_price * item.quantity

        else:
            for cart_item in cart_items:
                product = cart_item.product

                if cart_item.quantity > product.quantity_in_stock:
                    raise ProductOutOfStock

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=product.sale_price,
                    quantity=cart_item.quantity,
                )

                product.quantity_in_stock -= cart_item.quantity
                product.save(update_fields=["quantity_in_stock"])

                items_total += product.sale_price * cart_item.quantity

            cart_items.delete()

        # ================================
        # 5. DISCOUNT
        # ================================
        discount_amount = 0
        if payload.discount_code:
            discount = Discount.objects.filter(code=payload.discount_code).first()
            if not discount or not discount.is_available():
                raise DiscountDoesNotExists

            order.discount = discount
            discount_amount = (
                items_total * discount.value // 100
                if discount.type == "percent"
                else discount.value
            )

        # ================================
        # 6. UPDATE TOTAL
        # ================================
        order.discount_amount = discount_amount
        order.total_amount = items_total + order.shipping_fee - discount_amount
        order.save()

        # ================================
        # 7. CREATE PAYMENT
        # ================================

        payment = Payment.objects.create(
            order=order,
            code=generate_code(),
            method=payload.payment_method,
            amount=order.total_amount,
            status="PENDING",
        )

        # ================================
        # 8. SEND CONFIRMATION EMAIL
        # ================================
        send_order_confirmation_email(order=order, email=user.email)

        if payload.payment_method == "cod":
            return {
                "uid": order.uid,
                "code": order.code,
                "status": order.status,
                "total_amount": order.total_amount,
                "type": "cod",
                "message": SuccessMessage.CREATE_ORDER_SUCCESS,
                "payment_code": payment.code,
                "checkout": None,
            }

        elif payload.payment_method == "banking":
            return {
                "uid": order.uid,
                "code": order.code,
                "status": order.status,
                "total_amount": order.total_amount,
                "type": "banking",
                "message": SuccessMessage.CREATE_ORDER_SUCCESS,
                "payment_code": payment.code,
                "checkout": OrderORM.build_checkout_response(payment=payment),
            }
        raise ValueError("Unsupported payment method")

    @staticmethod
    def build_checkout_payload(payment: Payment) -> dict:
        merchant_id = os.environ.get("SEPAY_MERCHANT_ID")
        if not merchant_id:
            raise ValueError("Missing SEPAY_MERCHANT_ID")

        fields = {
            "merchant": merchant_id,
            "operation": "PURCHASE",
            "payment_method": "BANK_TRANSFER",
            "order_invoice_number": payment.code,
            "order_amount": str(int(payment.amount)),
            "currency": "VND",
            "order_description": f"Thanh toan don hang {payment.order.code}",
            "customer_id": str(payment.order.user.uid)
            if payment.order.user.uid
            else "",
            "success_url": os.environ.get("SEPAY_SUCCESS_URL", ""),
            "error_url": os.environ.get("SEPAY_ERROR_URL", ""),
            "cancel_url": os.environ.get("SEPAY_CANCEL_URL", ""),
            "custom_data": payment.code,
        }

        fields["signature"] = generate_signature(fields)
        return fields

    @staticmethod
    def build_checkout_response(payment) -> dict:
        return {
            "method": "POST",
            "action_url": "https://pay.sepay.vn/v1/checkout/init",
            "fields": OrderORM.build_checkout_payload(payment=payment),
        }

    @staticmethod
    @transaction.atomic
    def handle_sepay_webhook(payload: dict):
        payment_code = (
            payload.get("order_invoice_number")
            or payload.get("payment_code")
            or payload.get("custom_data")
        )

        if not payment_code:
            return {"error": "Missing payment code"}

        try:
            payment = Payment.objects.select_related("order").get(code=payment_code)
        except Payment.DoesNotExist:
            return {"error": "Payment not found"}

        status_value = str(payload.get("status", "")).lower()
        success_values = {"success", "completed", "paid", "succeeded"}

        if status_value in success_values:
            if payment.status != "COMPLETED":
                payment.status = "COMPLETED"
                payment.save(update_fields=["status"])

            order = payment.order
            if order.status != "CONFIRMED":
                order.status = "CONFIRMED"
                order.save(update_fields=["status"])

            return {"message": "Payment successful and order confirmed"}

        if status_value in {"failed", "error", "cancelled", "canceled"}:
            if payment.status != "FAILED":
                payment.status = "FAILED"
                payment.save(update_fields=["status"])
            return {"message": "Payment failed"}

        return {"message": "Webhook received", "payment_code": payment_code}

    @staticmethod
    def update_order_status(order: Order, payload: UpdateOrderStatusSchema):
        order.status = payload.status
        order.save(update_fields=["status"])

    @staticmethod
    def get_order_by_uid(uid: UUID) -> Order:
        try:
            return Order.objects.prefetch_related(
                Prefetch(
                    "order_item_fk_order",
                    queryset=OrderItem.objects.select_related(
                        "product"
                    ).prefetch_related(
                        Prefetch(
                            "product__image_fk_product",
                            queryset=ProductImage.objects.all(),
                            to_attr="images",
                        )
                    ),
                    to_attr="order_items",
                )
            ).get(uid=uid)
        except Order.DoesNotExist:
            raise OrderDoesNotExists

    @staticmethod
    def get_user_orders(user: User):
        return (
            Order.objects.filter(user=user)
            .prefetch_related(
                Prefetch(
                    "order_item_fk_order",
                    queryset=OrderItem.objects.select_related(
                        "product"
                    ).prefetch_related(
                        Prefetch(
                            "product__image_fk_product",
                            queryset=ProductImage.objects.all(),
                            to_attr="images",
                        )
                    ),
                    to_attr="order_items",
                )
            )
            .order_by("-order_date")
        )

    @staticmethod
    def get_admin_orders():
        return (
            Order.objects.all()
            .prefetch_related(
                Prefetch(
                    "order_item_fk_order",
                    queryset=OrderItem.objects.select_related(
                        "product"
                    ).prefetch_related(
                        Prefetch(
                            "product__image_fk_product",
                            queryset=ProductImage.objects.all(),
                            to_attr="images",
                        )
                    ),
                    to_attr="order_items",
                )
            )
            .order_by("-order_date")
        )

    @staticmethod
    def print_order(order: Order):
        order_items = order.order_item_fk_order.select_related("product").all()
        return generate_order_bill(order=order, order_items=order_items)

    @staticmethod
    def create_discount(payload: DiscountRequestSchema):
        discount = Discount(**payload.dict())
        discount.save()
        return discount

    @staticmethod
    def get_discount_by_uid(uid: UUID):
        try:
            discount = Discount.objects.get(uid=uid)
        except Discount.DoesNotExist:
            raise DiscountDoesNotExists

        return discount

    @staticmethod
    def get_discounts():
        discounts = Discount.objects.get(is_active=True)
        return discounts

    @staticmethod
    def update_discount(discount: Discount, payload: DiscountRequestSchema):
        for field, value in payload.dict().items():
            setattr(discount, field, value)
        discount.save()
        return discount
