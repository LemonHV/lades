import json
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from jwt import decode as jwt_decode

from django.conf import settings

from chat.services import ChatService
from account.models import User


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

        # lấy token từ query
        query = parse_qs(self.scope["query_string"].decode())
        token = query.get("token")

        if not token:
            await self.close()
            return

        # decode jwt
        self.user = await get_user_from_token(token[0])

        if not self.user:
            await self.close()
            return

        # lấy user_uid từ url
        self.user_uid = self.scope["url_route"]["kwargs"]["user_uid"]

        # kiểm tra quyền
        if not self.user.is_staff:
            if str(self.user.uid) != self.user_uid:
                await self.close()
                return

        # tạo room
        self.room_group_name = f"chat_{self.user_uid}"

        # join room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):

        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):

        try:
            data = json.loads(text_data)
        except Exception:
            return

        content = data.get("content")

        if not content:
            return

        service = ChatService()

        target_user = None

        # nếu admin thì lấy user đang chat
        if self.user.is_staff:
            target_user = await sync_to_async(
                lambda: User.objects.filter(uid=self.user_uid).first()
            )()

        # lưu message
        message = await sync_to_async(service.send_message)(
            sender=self.user,
            content=content,
            target_user=target_user
        )

        # broadcast
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": str(message.id),
                    "content": message.content,
                    "sender": str(message.sender.uid),
                    "created_at": str(message.created_at),
                }
            }
        )

    async def chat_message(self, event):

        await self.send(
            text_data=json.dumps(event["message"])
        )