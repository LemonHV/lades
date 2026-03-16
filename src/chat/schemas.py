from ninja import ModelSchema, Schema
from chat.models import Message, Notification, Conversation


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
    class Meta:
        model = Conversation
        fields = [
            "uid",
            "user",
            "last_message",
            "last_message_at",
            "created_at",
        ]
