from uuid import UUID
import os
from product.models import Product, ProductImage
from product.exceptions import ProductDoesNotExists, ProductOutOfStock
from order.utils import (
    generate_code,
    generate_order_bill,
    send_order_confirmation_email,
    build_sepay_qr_url,
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


class OrderORM:
    @staticmethod
    @transaction.atomic
    def create_order(user: User, payload: OrderRequestSchema):
        # ================================
        # 1. GET ITEMS
        # ================================
        buy_items = None
        cart_items = None

        if payload.source == "buy_now":
            buy_items = payload.order_items or []
            if not buy_items:
                raise ProductDoesNotExists
        else:
            cart_items = (
                CartItem.objects.select_related("product")
                .select_for_update()
                .filter(cart__user=user, uid__in=payload.cart_item_uids)
            )

            if not cart_items.exists():
                raise ProductDoesNotExists

        # ================================
        # 2. SHIPPING INFO
        # ================================
        try:
            shipping_info = ShippingInfo.objects.get(
                uid=payload.shipping_info_uid,
                user=user,
            )
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
            note=payload.note or "",
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
            product_uids = [item.product_uid for item in buy_items]

            products = Product.objects.select_for_update().in_bulk(
                product_uids,
                field_name="uid",
            )

            for item in buy_items:
                product = products.get(item.product_uid)
                if not product:
                    raise ProductDoesNotExists

                if item.quantity <= 0:
                    raise ProductOutOfStock

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

                if cart_item.quantity <= 0:
                    raise ProductOutOfStock

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
        # 5. APPLY DISCOUNT
        # ================================
        discount_amount = 0

        if payload.discount_code:
            discount = Discount.objects.filter(code=payload.discount_code).first()
            if not discount or not discount.is_available():
                raise DiscountDoesNotExists

            order.discount = discount

            if discount.type == "percent":
                discount_amount = items_total * discount.value // 100
            else:
                discount_amount = discount.value

            if discount_amount < 0:
                discount_amount = 0

            if discount_amount > items_total:
                discount_amount = items_total

        # ================================
        # 6. UPDATE ORDER TOTAL
        # ================================
        total_amount = items_total + order.shipping_fee - discount_amount
        if total_amount < 0:
            total_amount = 0

        order.discount_amount = discount_amount
        order.total_amount = total_amount
        order.save()

        # ================================
        # 7. CREATE PAYMENT
        # ================================
        payment = Payment.objects.create(
            order=order,
            method=payload.payment_method,
            amount=order.total_amount,
            status="PENDING",
            transfer_content="",
            qr_url="",
        )

        # ================================
        # 8. PAYMENT METHOD LOGIC
        # ================================
        if payload.payment_method == "cod":
            pass

        elif payload.payment_method == "banking":
            prefix = os.environ.get("PRE_DESCRIPTION", "DH102969").strip()

            payment.transfer_content = f"{prefix} {order.code}"
            payment.qr_url = build_sepay_qr_url(
                amount=payment.amount,
                order_code=order.code,
            )
            payment.save(update_fields=["transfer_content", "qr_url"])

        else:
            raise ValueError("Unsupported payment method")

        # ================================
        # 9. SEND EMAIL
        # ================================
        send_order_confirmation_email(order=order, email=user.email)

        # ================================
        # 10. RESPONSE
        # ================================
        return order

    @staticmethod
    def update_order_status(order: Order, payload: UpdateOrderStatusSchema):
        order.status = payload.status
        order.save(update_fields=["status"])

    @staticmethod
    def get_order_by_uid(uid: UUID) -> Order:
        try:
            return Order.objects.prefetch_related(
                Prefetch(
                    "order_item",
                    queryset=OrderItem.objects.select_related(
                        "product"
                    ).prefetch_related(
                        Prefetch(
                            "product__image",
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
                    "order_item",
                    queryset=OrderItem.objects.select_related(
                        "product"
                    ).prefetch_related(
                        Prefetch(
                            "product__image",
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
                    "order_item",
                    queryset=OrderItem.objects.select_related(
                        "product"
                    ).prefetch_related(
                        Prefetch(
                            "product__image",
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
        order_items = order.order_item.select_related("product").all()
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
