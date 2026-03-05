from chat.models import Conversation, Message
from account.models import User


class ChatORM:

    @staticmethod
    def get_or_create_conversation(user: User):
        conversation, _ = Conversation.objects.get_or_create(user=user)
        return conversation

    @staticmethod
    def get_conversation_by_user(user: User):
        return Conversation.objects.filter(user=user).first()

    @staticmethod
    def create_message(conversation: Conversation, sender: User, content: str):
        return Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content
        )

    @staticmethod
    def get_messages(conversation: Conversation):
        return conversation.messages.all().order_by("created_at")

    @staticmethod
    def mark_messages_as_read(conversation: Conversation, user: User):
        conversation.messages.exclude(sender=user).update(is_read=True)