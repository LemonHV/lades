import uuid
from django.db import models
from product.models import Product
from account.models import User
from django.utils.timezone import now
from order.utils import OrderStatus, PaymentStatus


class Payment(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        to="Order",
        on_delete=models.CASCADE,
        related_name="payment_fk_order",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )
    code = models.CharField(max_length=255)
    method = models.CharField(max_length=50)
    amount = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20, choices=PaymentStatus, default=PaymentStatus.PENDING
    )
    description = models.TextField(blank=True, null=True)
    payment_date = models.DateField(auto_now_add=True)
    provider_payment_id = models.CharField(max_length=100, null=True, blank=True)
    provider_response = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.amount}"


class Discount(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ("percent", "Percent"),
        ("fixed", "Fixed"),
    ]

    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, unique=True)
    type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    value = models.IntegerField()
    start_time = models.DateField(null=True, blank=True)
    end_time = models.DateField(null=True, blank=True)
    max_usage = models.IntegerField(null=True, blank=True)
    min_order_amount = models.IntegerField()

    def is_active(self):
        today = now().date()
        if self.start_time and self.start_time > today:
            return False
        if self.end_time and self.end_time < today:
            return False
        return True

    def is_available(self, order):
        today = now().date()
        if self.start_time and self.start_time > today:
            return False
        if self.end_time and self.end_time < today:
            return False
        if (
            self.max_usage is not None
            and self.count_number_of_usage() >= self.max_usage
        ):
            return False
        if self.min_order_amount is not None and order.total < self.min_order_amount:
            return False

        return True

    def calculate_discount_amount(self, amount: int):
        if self.type == "Percent":
            return amount * self.value / 100
        elif self.type == "Fixed":
            return self.value
        else:
            return 0

    def count_number_of_usage(self):
        return self.order_fk_discount.count()

    def __str__(self):
        return f"{self.name} ({self.code})"


class Order(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    order_date = models.DateField()
    receive_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50)
    total_amount = models.IntegerField()
    discount_amount = models.IntegerField(null=True, blank=True)
    shipping_fee = models.IntegerField()
    status = models.CharField(
        max_length=20, choices=OrderStatus, default=OrderStatus.PENDING
    )
    note = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="order_fk_user"
    )
    discount = models.ForeignKey(
        Discount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_fk_discount",
    )

    def calculate_total(self):
        items_total = sum(item.total_price() for item in self.order_item_fk_order.all())
        discount = self.discount_amount or 0
        return items_total - discount + self.shipping_fee

    def set_status(self, new_status):
        if new_status in dict(self.STATUS_CHOICES):
            self.status = new_status
            self.save(update_fields=["status"])

    def pending_count(self):
        return Order.objects.filter(status=OrderStatus.PENDING).count()

    def processing_count(self):
        return Order.objects.filter(status=OrderStatus.PROCESSING).count()

    def shipping_count(self):
        return Order.objects.filter(status=OrderStatus.SHIPPING).count()

    def completed_count(self):
        return Order.objects.filter(status=OrderStatus.COMPLETED).count()

    def cancelled_count(self):
        return Order.objects.filter(status=OrderStatus.CANCELLED).count()

    def __str__(self):
        return f"Order {self.code} - {self.status}"


class OrderItem(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        to=Order,
        on_delete=models.CASCADE,
        related_name="order_item_fk_order",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )
    product = models.ForeignKey(
        to=Product,
        on_delete=models.CASCADE,
        related_name="order_item_fk_product",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()

    @property
    def total_price(self):
        return self.price * self.quantity
