from uuid import UUID
from product.models import Product
from product.exceptions import ProductDoesNotExists, ProductOutOfStock
from order.utils import generate_code
from order.schemas import OrderRequestSchema
from order.models import Order, OrderItem, Discount
from django.utils.timezone import now
from django.db import transaction
from cart.models import CartItem
from account.models import User, ShippingInfo
from order.exceptions import (
    ShippingInfoDoesNotExists,
    OrderDoesNotExists,
    DiscountDoesNotExists,
)

from order.utils import OrderStatus


class OrderORM:
    @staticmethod
    @transaction.atomic
    def create_order(user: User, payload: OrderRequestSchema):
        # ================================
        # 1. GET ITEMS
        # ================================
        if payload.source == "buy_now":
            items = payload.order_items
        else:
            product_uids = [item.product_uid for item in payload.order_items]
            cart_items = CartItem.objects.select_related("product").filter(
                cart__user=user, product__uid__in=product_uids
            )
            items = cart_items

        # ================================
        # 2. SHIPPING INFO
        # ================================
        try:
            shipping_info = ShippingInfo.objects.get(id=payload.shipping_info_id)
        except ShippingInfo.DoesNotExist:
            raise ShippingInfoDoesNotExists

        # ================================
        # 3. CREATE ORDER (PENDING)
        # ================================
        order = Order.objects.create(
            code=generate_code(),
            order_date=now(),
            status="PENDING",
            shipping_fee=15000,
            discount_amount=0,
            total_amount=0,
            payment_method="cod",
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
                [item.product_uid for item in items],
                field_name="uid",
            )

            for item in items:
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
            for cart_item in items:
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
            if not discount or not discount.is_active():
                raise DiscountDoesNotExists
            order.discount = discount
            if discount.type == "percent":
                discount_amount = items_total * discount.value // 100
            else:
                discount_amount = discount.value

        # ================================
        # 6. UPDATE TOTAL
        # ================================
        order.discount_amount = discount_amount
        order.total_amount = items_total + order.shipping_fee - discount_amount
        order.save()

        return order

    @staticmethod
    def update_order_status(order: Order, status: OrderStatus):
        order.status = status
        order.save(update_fields=["status"])

    @staticmethod
    def get_order_by_uid(uid: UUID):
        try:
            order = Order.objects.prefetch_related("order_item_fk_order__product").get(
                uid=uid
            )
        except Order.DoesNotExist:
            raise OrderDoesNotExists

        return order

    @staticmethod
    def get_user_orders(user: User):
        orders = Order.objects.filter(user=user).exclude(status="pending")
        return orders
