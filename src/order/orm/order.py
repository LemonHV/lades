from uuid import UUID
from product.models import Product
from product.exceptions import ProductDoesNotExists, ProductOutOfStock
from order.utils import generate_code, generate_order_bill
from order.schemas import OrderRequestSchema, DiscountRequestSchema
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
