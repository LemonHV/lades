from pydantic import BaseModel

from account.models import User
from chat.schemas import MessageSchema, NotificationSchema, UploadImageResponseSchema, ConversationSchema
from chat.services import ChatService, NotificationService
from chat.utils import MessageType
from router.authenticate import AuthBear
from router.authorize import IsAdmin
from router.controller import Controller, api, get, post
from router.types import AuthenticatedRequest


class SendMessageBody(BaseModel):
    content: str
    type: str = MessageType.TEXT


@api(prefix_or_class="chats", tags=["Chat"], auth=AuthBear())
class ChatAPI(Controller):
    def __init__(self, service: ChatService):
        self.service = service

    @post("/{user_uid}/messages", response=MessageSchema)
    def send_message(
        self,
        request: AuthenticatedRequest,
        user_uid: str,
        payload: SendMessageBody,
    ):
        sender = request.user
        target_user = None

        if not payload.content.strip():
            return 400, {"detail": "Content is required"}

        if sender.is_staff:
            target_user = User.objects.filter(uid=user_uid).first()
            if not target_user:
                return 404, {"detail": "User not found"}
        else:
            if str(sender.uid) != user_uid:
                return 403, {"detail": "Permission denied"}

        return self.service.send_message(
            sender=sender,
            content=payload.content,
            target_user=target_user,
            message_type=payload.type,
        )

    @get(
        "/conversations",
        response=list[ConversationSchema],
        auth=AuthBear(),
        permissions=[IsAdmin()],
    )
    def get_conversations(self):
        conversations = self.service.get_conversations()
        return conversations

    @get("/{user_uid}/messages", response=list[MessageSchema])
    def get_messages(
        self,
        request: AuthenticatedRequest,
        user_uid: str,
    ):
        user = request.user
        target_user = None

        if user.is_staff:
            target_user = User.objects.filter(uid=user_uid).first()
            if not target_user:
                return 404, {"detail": "User not found"}
        else:
            if str(user.uid) != user_uid:
                return 403, {"detail": "Permission denied"}

        return self.service.get_messages(
            user=user,
            target_user=target_user,
        )

    @post("/{user_uid}/mark-read")
    def mark_as_read(
        self,
        request: AuthenticatedRequest,
        user_uid: str,
    ):
        user = request.user
        target_user = None

        if user.is_staff:
            target_user = User.objects.filter(uid=user_uid).first()
            if not target_user:
                return 404, {"detail": "User not found"}
        else:
            if str(user.uid) != user_uid:
                return 403, {"detail": "Permission denied"}

        updated_count = self.service.mark_as_read(
            user=user,
            target_user=target_user,
        )

        return {
            "detail": "Marked as read",
            "updated_count": updated_count,
        }

    @post("/images", auth=AuthBear(), response=UploadImageResponseSchema)
    def send_image_message(self, request: AuthenticatedRequest):
        image_file = request.FILES.get("file")
        image_url = self.service.send_image_message(image_file=image_file)
        return {"image_url": image_url}


@api(prefix_or_class="notifications", tags=["Notification"], auth=AuthBear())
class NotificationAPI(Controller):
    def __init__(self, service: NotificationService):
        self.service = service

    # Lấy danh sách notification
    @get("/", response=list[NotificationSchema])
    def get_notifications(self, request: AuthenticatedRequest):
        return self.service.get_notifications(request.user)

    # Đánh dấu đã đọc
    @post("/{notification_uid}/read")
    def mark_as_read(self, request: AuthenticatedRequest, notification_uid: str):
        updated = self.service.mark_as_read(notification_uid, request.user)

        return {"detail": "Marked as read", "updated": updated}

    # Đánh dấu đọc tất cả
    @post("/read-all")
    def mark_all_as_read(self, request: AuthenticatedRequest):
        updated = self.service.mark_all_as_read(request.user)

        return {"detail": "All notifications marked as read", "updated": updated}
