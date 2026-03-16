from chat.orm.chat import ChatORM
from account.models import User
from chat.models import Conversation
from chat.utils import MessageType


class ChatService:
    def __init__(self):
        self.orm = ChatORM()

    def get_or_create_conversation(self, user: User) -> Conversation:
        return self.orm.get_or_create_conversation(user)

    def get_conversation(self, user: User) -> Conversation:
        return self.orm.get_conversation_by_user(user)

    def send_message(
        self,
        sender: User,
        content: str,
        target_user: User = None,
        message_type: str = MessageType.TEXT,
    ):
        if sender.is_staff:
            if not target_user:
                raise ValueError("Admin must provide target_user")
            conversation = self.orm.get_or_create_conversation(target_user)
        else:
            conversation = self.orm.get_or_create_conversation(sender)

        return self.orm.create_message(
            conversation=conversation,
            sender=sender,
            content=content,
            message_type=message_type,
        )

    def get_messages(self, user: User, target_user: User = None):
        if user.is_staff:
            if not target_user:
                raise ValueError("Admin must provide target_user")
            conversation = self.orm.get_conversation_by_user(target_user)
        else:
            conversation = self.orm.get_conversation_by_user(user)

        if not conversation:
            return []

        return self.orm.get_messages(conversation)

    def mark_as_read(self, user: User, target_user: User = None):
        if user.is_staff:
            if not target_user:
                return 0
            conversation = self.orm.get_conversation_by_user(target_user)
        else:
            conversation = self.orm.get_conversation_by_user(user)

        if not conversation:
            return 0

        return self.orm.mark_messages_as_read(conversation, user)
