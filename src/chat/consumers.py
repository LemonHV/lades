import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.room_user_uid = self.scope["url_route"]["kwargs"]["user_uid"]

        if not self.user.is_authenticated:
            await self.close()
            return

        if not self.user.is_staff:
            if str(self.user.uid) != self.room_user_uid:
                await self.close()
                return

        self.room_group_name = f"user_{self.room_user_uid}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "user": self.user.email,
                "is_staff": self.user.is_staff,
            },
        )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "user": event["user"],
                    "is_staff": event["is_staff"],
                }
            )
        )
