import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")

        # 1️⃣ Phải đăng nhập
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.user = user

        # 2️⃣ Nếu là staff → được chọn room theo URL
        if self.user.is_staff:
            self.room_user_uid = self.scope["url_route"]["kwargs"].get("user_uid")
            if not self.room_user_uid:
                await self.close()
                return
        else:
            # 3️⃣ User thường → chỉ được vào phòng của chính mình
            self.room_user_uid = str(self.user.uid)

        self.room_group_name = f"user_{self.room_user_uid}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        if not hasattr(self, "room_group_name"):
            return

        try:
            data = json.loads(text_data)
            message = data.get("message")
        except Exception:
            return

        if not message:
            return

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