from datetime import datetime
from uuid import UUID

from ninja import ModelSchema, Schema

from chat.models import Conversation, Message, Notification


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


class UserResponseSchema(Schema):
    uid: UUID
    name: str
    email: str


class LastMessageSchema(Schema):
    uid: UUID
    type: str
    content: str
    is_read: bool
    created_at: datetime


class ConversationSchema(ModelSchema):
    sender: UserResponseSchema
    last_message: LastMessageSchema | None

    class Meta:
        model = Conversation
        fields = [
            "uid",
            "created_at",
        ]

    @staticmethod
    def resolve_sender(obj):
        return obj.user

    @staticmethod
    def resolve_last_message(obj):
        return obj.last_message
