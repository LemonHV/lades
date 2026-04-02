from enum import unique

from django.db.models import TextChoices


@unique
class MessageType(TextChoices):
    TEXT = "TEXT", "Text"
    IMAGE = "IMAGE", "Image"
    PRODUCT = "PRODUCT", "Product"
    
    
@unique
class NotificationType(TextChoices):
    NEW_MESSAGE = "NEW_MESSAGE", "New Message"
    NEW_ORDER = "NEW_ORDER", "New Order"
    SYSTEM = "SYSTEM", "System Notification"

