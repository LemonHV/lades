from chat.models import Conversation, Message
from account.models import User
from chat.utils import MessageType
from product.utils import upload_file
import secrets


class ChatORM:
    @staticmethod
    def get_or_create_conversation(user: User):
        conversation, _ = Conversation.objects.get_or_create(user=user)
        return conversation

    @staticmethod
    def get_conversation_by_user(user: User):
        return Conversation.objects.filter(user=user).first()

    @staticmethod
    def create_message(
        conversation: Conversation,
        sender: User,
        content: str,
        message_type: str = MessageType.TEXT,
    ):
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content,
            type=message_type,
        )
        conversation.last_message = message
        conversation.last_message_at = message.created_at
        conversation.save(update_fields=["last_message", "last_message_at"])

        return message

    @staticmethod
    def get_messages(conversation: Conversation):
        return conversation.message_fk_conversation.all().order_by("created_at")

    @staticmethod
    def mark_messages_as_read(conversation: Conversation, user: User):
        return (
            conversation.message_fk_conversation.filter(is_read=False)
            .exclude(sender=user)
            .update(is_read=True)
        )

    @staticmethod
    def send_image_message(image_file):
        if not image_file:
            raise ValueError("Image file is required")
        image_info = upload_file(
            file=image_file,
            folder="chat_images/",
            public_id=f"chat_{secrets.token_urlsafe(16)}",
            overwrite=True,
        )
        return image_info.get("secure_url")
