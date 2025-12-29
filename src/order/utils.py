import random
import string

from enum import unique

from django.db.models import TextChoices


@unique
class OrderStatus(TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    SHIPPING = "SHIPPING", "Shipping"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


@unique
class PaymentStatus(TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


def generate_code(length=20):
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))
