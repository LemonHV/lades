from ninja import ModelSchema, Schema
from chat.models import Message, Notification


class MessageSchema(ModelSchema):
    sender_uid: str
    sender_name: str

    class Meta:
        model = Message
        fields = [
            "uid",
            "content",
            "type",
            "is_read",
            "created_at",
        ]

    @staticmethod
    def resolve_sender_uid(obj):
        return str(obj.sender.uid)

    @staticmethod
    def resolve_sender_name(obj):
        return obj.sender.name


class NotificationSchema(ModelSchema):
    class Meta:
        model = Notification
        fields = [
            "uid",
            "type",
            "title",
            "is_read",
            "created_at",
        ]


class UploadImageResponseSchema(Schema):
    image_url: str


class ConversationSchema(ModelSchema):
    user_uid: str
    user_name: str
    last_message_content: str | None
    last_message_type: str | None
    last_message_at: str | None

    class Meta:
        model = Message
        fields = []

    @staticmethod
    def resolve_user_uid(obj):
        return str(obj.user.uid)

    @staticmethod
    def resolve_user_name(obj):
        return obj.user.name

    @staticmethod
    def resolve_last_message_content(obj):
        return obj.last_message.content if obj.last_message else None

    @staticmethod
    def resolve_last_message_type(obj):
        return obj.last_message.type if obj.last_message else None

    @staticmethod
    def resolve_last_message_at(obj):
        return obj.last_message_at.isoformat() if obj.last_message_at else None