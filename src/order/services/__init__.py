from order.orm.order import OrderORM
from order.models import Order
from order.schemas import OrderRequestSchema
from order.exceptions import OrderDoesNotExists
from order.utils import OrderStatus
from account.models import User
from uuid import UUID


class OrderService:
    def __init__(self):
        self.orm = OrderORM()

    def create_order(self, user: User, payload: OrderRequestSchema):
        return self.orm.create_order(user=user, payload=payload)

    def update_order_status(self, uid: UUID, status: OrderStatus):
        try:
            order = Order.objects.get(uid=uid)
        except Order.DoesNotExist:
            raise OrderDoesNotExists
        self.orm.update_order_status(order=order, status=status)

    def get_order_by_uid(self, uid: UUID):
        return self.orm.get_order_by_uid(uid=uid)

    def get_user_orders(self, user: User):
        return self.orm.get_user_orders(user=user)
