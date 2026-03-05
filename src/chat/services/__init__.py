from chat.orm.chat import ChatORM
from account.models import User
from chat.models import Conversation


class ChatService:

    def __init__(self):
        self.orm = ChatORM()

    # Lấy hoặc tạo conversation cho user
    def get_or_create_conversation(self, user: User) -> Conversation:
        return self.orm.get_or_create_conversation(user)

    # Lấy conversation theo user
    def get_conversation(self, user: User) -> Conversation:
        return self.orm.get_conversation_by_user(user)

    # Gửi tin nhắn
    def send_message(self, sender: User, content: str, target_user: User = None):
        """
        Nếu sender là admin -> phải truyền target_user
        Nếu sender là user -> tự lấy conversation của chính họ
        """

        if sender.is_staff:
            if not target_user:
                raise ValueError("Admin must provide target_user")

            conversation = self.orm.get_or_create_conversation(target_user)
        else:
            conversation = self.orm.get_or_create_conversation(sender)

        return self.orm.create_message(
            conversation=conversation,
            sender=sender,
            content=content
        )

    # Lấy danh sách tin nhắn
    def get_messages(self, user: User, target_user: User = None):
        """
        User thường -> xem chat của chính họ
        Admin -> truyền target_user để xem chat của user đó
        """

        if user.is_staff:
            if not target_user:
                raise ValueError("Admin must provide target_user")

            conversation = self.orm.get_conversation_by_user(target_user)
        else:
            conversation = self.orm.get_conversation_by_user(user)

        if not conversation:
            return []

        return self.orm.get_messages(conversation)

    # Đánh dấu đã đọc
    def mark_as_read(self, user: User, target_user: User = None):
        if user.is_staff:
            conversation = self.orm.get_conversation_by_user(target_user)
        else:
            conversation = self.orm.get_conversation_by_user(user)

        if conversation:
            self.orm.mark_messages_as_read(conversation, user)