from account.models import User
from chat.models import Conversation
from chat.orm.chat import ChatORM
from chat.orm.notification import NotificationORM
from chat.utils import MessageType, NotificationType


class ChatService:
    def __init__(self):
        self.orm = ChatORM()

    def get_or_create_conversation(self, user: User) -> Conversation:
        return self.orm.get_or_create_conversation(user)

    def get_conversations(self):
        return self.orm.get_conversations()

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

    def send_image_message(self, image_file):
        return self.orm.send_image_message(image_file)
class NotificationService:
    def __init__(self):
        self.orm = NotificationORM()

    def create_notification(
        self,
        user: User,
        title: str,
        notification_type: str = NotificationType.NEW_MESSAGE,
    ):
        return self.orm.create_notification(
            user=user, title=title, notification_type=notification_type
        )

    def get_notifications(self, user: User):
        return self.orm.get_notifications(user)

    def mark_as_read(self, notification_uid: str, user: User):
        return self.orm.mark_as_read(notification_uid, user)

    def mark_all_as_read(self, user: User):
        return self.orm.mark_all_as_read(user)
