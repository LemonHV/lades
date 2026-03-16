import json
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from jwt import decode as jwt_decode

from account.models import User
from chat.services import ChatService
from utils import MessageType


async def get_user_from_token(token):
    try:
        decoded = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        user = await sync_to_async(
            lambda: User.objects.filter(uid=decoded.get("user_id")).first()
        )()
        return user
    except Exception:
        return None


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query = parse_qs(self.scope["query_string"].decode())
        token = query.get("token")

        if not token:
            await self.close(code=4001)
            return

        self.user = await get_user_from_token(token[0])

        if not self.user:
            await self.close(code=4002)
            return

        self.user_uid = self.scope["url_route"]["kwargs"]["user_uid"]

        # user thường chỉ được vào room của chính họ
        if not self.user.is_staff and str(self.user.uid) != self.user_uid:
            await self.close(code=4003)
            return

        self.room_group_name = f"chat_{self.user_uid}"
        self.service = ChatService()

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # khi vừa connect có thể đánh dấu các tin nhắn bên kia gửi là đã đọc
        await self._mark_messages_as_read()

        await self.send(
            text_data=json.dumps(
                {
                    "event": "connected",
                    "room": self.room_group_name,
                    "user_uid": str(self.user.uid),
                }
            )
        )

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except Exception:
            await self._send_error("Invalid JSON")
            return

        event = data.get("event", "message")

        if event == "message":
            await self.handle_send_message(data)
        elif event == "mark_read":
            await self.handle_mark_read(data)
        elif event == "ping":
            await self.send(text_data=json.dumps({"event": "pong"}))
        else:
            await self._send_error("Unsupported event")

    async def handle_send_message(self, data):
        content = (data.get("content") or "").strip()
        message_type = data.get("type", MessageType.TEXT)

        if not content:
            await self._send_error("Content is required")
            return

        if message_type not in [choice[0] for choice in MessageType]:
            await self._send_error("Invalid message type")
            return

        target_user = None

        if self.user.is_staff:
            target_user = await sync_to_async(
                lambda: User.objects.filter(uid=self.user_uid).first()
            )()

            if not target_user:
                await self._send_error("Target user not found")
                return

        try:
            message = await sync_to_async(self.service.send_message)(
                sender=self.user,
                content=content,
                target_user=target_user,
                message_type=message_type,
            )
        except Exception:
            await self._send_error("Failed to save message")
            return

        payload = {
            "event": "message",
            "message": {
                "uid": str(message.uid),
                "conversation_uid": str(message.conversation.uid),
                "sender_uid": str(message.sender.uid),
                "sender_name": getattr(message.sender, "username", ""),
                "type": message.type,
                "content": message.content,
                "is_read": message.is_read,
                "created_at": message.created_at.isoformat(),
            },
        }

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "payload": payload,
            },
        )

    async def handle_mark_read(self, data):
        message_uid = data.get("message_uid")

        try:
            updated_count = await sync_to_async(self.service.mark_messages_as_read)(
                room_user_uid=self.user_uid,
                current_user=self.user,
                message_uid=message_uid,
            )
        except Exception:
            await self._send_error("Failed to mark read")
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_read",
                "payload": {
                    "event": "read",
                    "message_uid": message_uid,
                    "updated_count": updated_count,
                    "reader_uid": str(self.user.uid),
                },
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    async def chat_read(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    async def _mark_messages_as_read(self):
        try:
            await sync_to_async(self.service.mark_messages_as_read)(
                room_user_uid=self.user_uid,
                current_user=self.user,
                message_uid=None,
            )
        except Exception:
            pass

    async def _send_error(self, message):
        await self.send(
            text_data=json.dumps(
                {
                    "event": "error",
                    "message": message,
                }
            )
        )