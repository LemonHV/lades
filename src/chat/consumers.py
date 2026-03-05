import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async

from chat.services import ChatService
from account.models import User


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]

        if not self.user or isinstance(self.user, AnonymousUser):
            await self.close()
            return

        self.user_uid = self.scope["url_route"]["kwargs"]["user_uid"]
        self.room_group_name = f"chat_{self.user_uid}"

        # Permission check
        if not self.user.is_staff:
            if str(self.user.uid) != self.user_uid:
                await self.close()
                return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data.get("content")

        if not content:
            return

        service = ChatService()

        # Lấy target_user nếu là admin
        target_user = None
        if self.user.is_staff:
            target_user = await sync_to_async(
                User.objects.filter(uid=self.user_uid).first
            )()

        message = await sync_to_async(service.send_message)(
            sender=self.user,
            content=content,
            target_user=target_user
        )

        # Broadcast message
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": message.id,
                    "content": message.content,
                    "sender": message.sender.id,
                    "created_at": str(message.created_at),
                }
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))