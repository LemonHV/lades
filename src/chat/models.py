from django.db import models
from account.models import User
from chat.utils import MessageType, NotificationType
from uuid import uuid4


class Conversation(models.Model):
    uid = models.UUIDField(default=uuid4, unique=True, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="conversation"
    )
    last_message = models.ForeignKey(
        "Message",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Chat with {self.user.name}"


class Message(models.Model):
    uid = models.UUIDField(default=uuid4, unique=True, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="message"
    )

    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=20, choices=MessageType, default=MessageType.TEXT
    )
    content = models.TextField(blank=True, default="")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.name}: {self.content[:20]}"


class Notification(models.Model):
    uid = models.UUIDField(default=uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notification"
    )
    type = models.CharField(max_length=20, choices=NotificationType)
    title = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.name} - {self.title}"
