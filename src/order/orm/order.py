import os
from uuid import UUID

from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils.timezone import now

from account.models import ShippingInfo, User
from cart.models import CartItem
from order.exceptions import (
    DiscountDoesNotExists,
    OrderDoesNotExists,
    ShippingInfoDoesNotExists,
)
from order.models import Discount, Order, OrderItem, Payment, ShippingMethod
from order.schemas import (
    DiscountRequestSchema,
    OrderRequestSchema,
    UpdateOrderStatusSchema,
)
from order.utils import (
    build_sepay_qr_url,
    generate_code,
    generate_order_bill,
    send_order_confirmation_email,
)
from product.exceptions import ProductDoesNotExists, ProductOutOfStock
from product.models import Product, ProductImage


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
            cart_items = list(
                CartItem.objects.select_related("product")
                .select_for_update()
                .filter(cart__user=user, uid__in=payload.cart_item_uids)
            )

            if not cart_items:
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
        # 3. PREPARE & LOCK PRODUCTS
        # ================================
        if payload.source == "buy_now":
            product_uids = [item.product_uid for item in buy_items]
        else:
            product_uids = [cart_item.product.uid for cart_item in cart_items]

        products = Product.objects.select_for_update().in_bulk(
            product_uids,
            field_name="uid",
        )

        if payload.source == "buy_now":
            for item in buy_items:
                product = products.get(item.product_uid)
                if not product:
                    raise ProductDoesNotExists

                if item.quantity <= 0:
                    raise ProductOutOfStock

                if item.quantity > product.quantity_in_stock:
                    raise ProductOutOfStock
        else:
            for cart_item in cart_items:
                product = products.get(cart_item.product.uid)
                if not product:
                    raise ProductDoesNotExists

                if cart_item.quantity <= 0:
                    raise ProductOutOfStock

                if cart_item.quantity > product.quantity_in_stock:
                    raise ProductOutOfStock

        # ================================
        # 4. CREATE ORDER
        # ================================
        order = Order.objects.create(
            code=generate_code(),
            shipping_method=payload.shipping_method,
            shipping_fee=ShippingMethod.get_fee(payload.shipping_method),
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
        # 5. CREATE ORDER ITEMS + DEDUCT STOCK
        # ================================
        if payload.source == "buy_now":
            for item in buy_items:
                product = products[item.product_uid]

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=product.sale_price,
                    quantity=item.quantity,
                )

                product.quantity_in_stock -= item.quantity
                product.save(update_fields=["quantity_in_stock"])
        else:
            for cart_item in cart_items:
                product = products[cart_item.product.uid]

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=product.sale_price,
                    quantity=cart_item.quantity,
                )

                product.quantity_in_stock -= cart_item.quantity
                product.save(update_fields=["quantity_in_stock"])

            CartItem.objects.filter(uid__in=[item.uid for item in cart_items]).delete()

        # ================================
        # 6. APPLY DISCOUNT
        # ================================
        if payload.discount_code:
            discount = (
                Discount.objects.select_for_update()
                .filter(code=payload.discount_code)
                .first()
            )
            if not discount:
                raise DiscountDoesNotExists

            if not discount.is_available_for_order(order):
                raise DiscountDoesNotExists

            order.discount = discount
            order.discount_amount = discount.calculate_discount_amount(order.subtotal)

        # ================================
        # 7. UPDATE ORDER TOTAL
        # ================================
        order.refresh_total_amount(save=False)
        order.save()

        # ================================
        # 8. CREATE PAYMENT
        # ================================
        payment = Payment.objects.create(
            order=order,
            method=payload.payment_method,
            amount=order.total_amount,
            transfer_content="",
            qr_url="",
        )

        # ================================
        # 9. PAYMENT METHOD LOGIC
        # ================================
        if payload.payment_method == "cod":
            send_order_confirmation_email(order=order, email=user.email)

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

        return order

    @staticmethod
    def update_order_status(order: Order, payload: UpdateOrderStatusSchema):
        order.set_status(payload.status)

    @staticmethod
    def get_order_by_uid(uid: UUID) -> Order:
        try:
            return Order.objects.prefetch_related(
                Prefetch(
                    "items",
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
                    "items",
                    queryset=OrderItem.objects.select_related(
                        "product"
                    ).prefetch_related(
                        Prefetch(
                            "product__product_images",
                            queryset=ProductImage.objects.select_related("attachment"),
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
                    "items",
                    queryset=OrderItem.objects.select_related(
                        "product"
                    ).prefetch_related(
                        Prefetch(
                            "product__product_images",
                            queryset=ProductImage.objects.select_related("attachment"),
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
        return Discount.objects.create(**payload.dict())

    @staticmethod
    def get_discount_by_uid(uid: UUID):
        return Discount.objects.filter(uid=uid).first()

    @staticmethod
    def get_discounts():
        today = now()

        return Discount.objects.filter(
            Q(start_time__lte=today) | Q(start_time__isnull=True),
            Q(end_time__gte=today) | Q(end_time__isnull=True),
        )

    @staticmethod
    def update_discount(discount: Discount, payload: DiscountRequestSchema):
        for field, value in payload.dict().items():
            setattr(discount, field, value)
        discount.save()
        return discount
