from chat.services import ChatService
from chat.schemas import MessageSchema
from account.models import User
from router.authenticate import AuthBear
from router.controller import Controller, api, get, post
from router.types import AuthenticatedRequest


@api(prefix_or_class="chats", tags=["Chat"], auth=AuthBear())
class ChatAPI(Controller):

    def __init__(self, service: ChatService):
        self.service = service

    # =====================================
    # 1️⃣ Gửi tin nhắn
    # =====================================
    @post("/{user_uid}/messages", response=MessageSchema)
    def send_message(
        self,
        request: AuthenticatedRequest,
        user_uid: str,
        content: str
    ):
        sender = request.user
        target_user = None

        if sender.is_staff:
            target_user = User.objects.filter(uid=user_uid).first()
            if not target_user:
                return 404, {"detail": "User not found"}
        else:
            # User chỉ được chat với chính mình
            if str(sender.uid) != user_uid:
                return 403, {"detail": "Permission denied"}

        return self.service.send_message(
            sender=sender,
            content=content,
            target_user=target_user
        )

    # =====================================
    # 2️⃣ Lấy danh sách tin nhắn
    # =====================================
    @get("/{user_uid}/messages", response=list[MessageSchema])
    def get_messages(
        self,
        request: AuthenticatedRequest,
        user_uid: str
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
            target_user=target_user
        )

    # =====================================
    # 3️⃣ Đánh dấu đã đọc
    # =====================================
    @post("/{user_uid}/mark-read")
    def mark_as_read(
        self,
        request: AuthenticatedRequest,
        user_uid: str
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

        self.service.mark_as_read(
            user=user,
            target_user=target_user
        )

        return {"detail": "Marked as read"}