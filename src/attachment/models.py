from django.db import models
from enum import unique
from uuid import uuid4


@unique
class AttachmentType(models.TextChoices):
    PRODUCT = "PRODUCT", "Product"
    MESSAGE = "MESSAGE", "Message"
    REVIEW = "REVIEW", "Review"


class Attachment(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    type = models.CharField(
        max_length=20,
        choices=AttachmentType.choices,
    )

    url = models.URLField(max_length=500)
    public_id = models.CharField(max_length=255, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
