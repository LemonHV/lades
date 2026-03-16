from chat.models import Conversation, Message
from account.models import User
from chat.utils import MessageType


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
