from django.db import models
from account.models import User


class ChatThread(models.Model):
    customer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="thread_fk_customer"
    )
    admin = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="thread_fk_admin"
    )


class Message(models.Model):
    thread = models.ForeignKey(
        ChatThread, on_delete=models.CASCADE, related_name="message_fk_thread"
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
