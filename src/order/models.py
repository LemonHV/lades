import uuid

from django.db import models
from django.utils.timezone import now

from django.core.exceptions import ValidationError
from account.models import User
from order.utils import OrderStatus, PaymentStatus
from product.models import Product


class DiscountType(models.TextChoices):
    PERCENT = "percent", "Percent"
    FIXED = "fixed", "Fixed"


class ShippingMethod(models.TextChoices):
    STANDARD = "standard", "Standard Shipping"
    EXPRESS = "express", "Express Shipping"
    SAVE = "save", "Save Shipping"

    @classmethod
    def get_fee(cls, method: str) -> int:
        return {
            cls.STANDARD: 20000,
            cls.EXPRESS: 40000,
            cls.SAVE: 10000,
        }.get(method, 0)


class Discount(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    type = models.CharField(max_length=10, choices=DiscountType.choices)
    value = models.PositiveIntegerField()
    start_time = models.DateField(null=True, blank=True)
    end_time = models.DateField(null=True, blank=True)
    max_usage = models.PositiveIntegerField(null=True, blank=True)
    min_order_amount = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValidationError("start_time cannot be greater than end_time.")

        if self.type == DiscountType.PERCENT and self.value > 100:
            raise ValidationError("Percent discount cannot exceed 100%.")

    @property
    def is_active(self) -> bool:
        today = now().date()
        if self.start_time and self.start_time > today:
            return False
        if self.end_time and self.end_time < today:
            return False
        return True

    @property
    def usage_count(self) -> int:
        return self.orders.count()

    def is_available_for_order(self, order: "Order") -> bool:
        if not self.is_active:
            return False

        if self.max_usage is not None and self.usage_count >= self.max_usage:
            return False

        if order.subtotal < self.min_order_amount:
            return False

        return True

    def calculate_discount_amount(self, amount: int) -> int:
        if amount <= 0:
            return 0

        if self.type == DiscountType.PERCENT:
            return int(amount * self.value / 100)

        if self.type == DiscountType.FIXED:
            return min(self.value, amount)

        return 0

    def __str__(self):
        return f"{self.name} ({self.code})"


class OrderQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(status=OrderStatus.PENDING)

    def processing(self):
        return self.filter(status=OrderStatus.PROCESSING)

    def shipping(self):
        return self.filter(status=OrderStatus.SHIPPING)

    def completed(self):
        return self.filter(status=OrderStatus.COMPLETED)

    def cancelled(self):
        return self.filter(status=OrderStatus.CANCELLED)


class Order(models.Models):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True, db_index=True)
    order_date = models.DateField(default=now)
    receive_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50)
    total_amount = models.PositiveIntegerField(default=0)
    discount_amount = models.PositiveIntegerField(default=0)
    shipping_method = models.CharField(
        max_length=20, choices=ShippingMethod.choices, default=ShippingMethod.STANDARD
    )
    shipping_fee = models.PositiveIntegerField(
        default=ShippingMethod.get_fee(ShippingMethod.STANDARD)
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus,
        default=OrderStatus.PENDING,
        db_index=True,
    )
    note = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    discount = models.ForeignKey(
        Discount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OrderQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    @property
    def subtotal(self) -> int:
        return sum(item.total_price for item in self.items.all())

    def calculate_total(self) -> int:
        return max(self.subtotal - (self.discount_amount or 0) + self.shipping_fee, 0)

    def refresh_total_amount(self, save: bool = True) -> int:
        self.total_amount = self.calculate_total()
        if save:
            self.save(update_fields=["total_amount", "updated_at"])
        return self.total_amount

    def set_status(self, new_status: str, save: bool = True) -> None:
        valid_statuses = {choice[0] for choice in OrderStatus}
        if new_status not in valid_statuses:
            raise ValidationError(f"Invalid status: {new_status}")

        self.status = new_status
        if save:
            self.save(update_fields=["status", "updated_at"])

    @classmethod
    def status_counts(cls) -> dict:
        return {
            "pending": cls.objects.pending().count(),
            "processing": cls.objects.processing().count(),
            "shipping": cls.objects.shipping().count(),
            "completed": cls.objects.completed().count(),
            "cancelled": cls.objects.cancelled().count(),
        }

    def __str__(self):
        return f"Order {self.code} - {self.status}"


class OrderItem(models.Models):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        to_field="uid",
        db_index=True,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="order_items",
        to_field="uid",
        db_index=True,
    )
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    @property
    def total_price(self) -> int:
        return self.price * self.quantity

    def __str__(self):
        return f"{self.order.code} - {self.product} x {self.quantity}"


class Payment(models.Models):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="payment",
        to_field="uid",
    )
    method = models.CharField(max_length=50)
    amount = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    transfer_content = models.CharField(max_length=255, null=True, blank=True)
    qr_url = models.TextField(blank=True, default="")
    sepay_transaction_id = models.BigIntegerField(null=True, blank=True, unique=True)
    sepay_reference_code = models.CharField(max_length=100, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    raw_payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def mark_as_paid(self, paid_time=None, save: bool = True) -> None:
        self.status = PaymentStatus.PAID
        self.paid_at = paid_time or now()
        if save:
            self.save(update_fields=["status", "paid_at", "updated_at"])

    def __str__(self):
        return f"{self.order.code} - {self.amount}"
