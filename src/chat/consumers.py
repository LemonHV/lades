import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")

        if not user or not user.is_authenticated:
            await self.close()
            return

        self.user = user
        self.room_group_name = None

        # 👤 User thường → auto join phòng của chính họ
        if not self.user.is_staff:
            self.room_group_name = f"user_{self.user.uid}"

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name,
            )

        await self.accept()

    async def disconnect(self, close_code):
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except Exception:
            return

        # =========================
        # 👑 ADMIN JOIN ROOM
        # =========================
        if self.user.is_staff and "join_room" in data:
            room_uid = data["join_room"]

            new_room = f"user_{room_uid}"

            # Nếu đang ở room khác thì rời trước
            if self.room_group_name:
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name,
                )

            self.room_group_name = new_room

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name,
            )

            return

        # =========================
        # 💬 GỬI MESSAGE
        # =========================
        message = data.get("message")

        if not message or not self.room_group_name:
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

    # =========================
    # 📡 BROADCAST HANDLER
    # =========================
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