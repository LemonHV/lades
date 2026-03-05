from ninja import ModelSchema
from chat.models import Message


class MessageSchema(ModelSchema):

    class Meta:
        model = Message
        fields = ["id", "content", "created_at", "is_read"]