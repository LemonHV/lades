from account.models import User
from chat.models import Notification
from chat.utils import NotificationType


class NotificationORM:

    @staticmethod
    def create_notification(
        user: User,
        title: str,
        notification_type: str = NotificationType.NEW_MESSAGE
    ):
        return Notification.objects.create(
            user=user,
            title=title,
            type=notification_type
        )

    @staticmethod
    def get_notifications(user: User):
        return Notification.objects.filter(user=user).order_by("-created_at")

    @staticmethod
    def mark_as_read(notification_uid: str, user: User):
        return Notification.objects.filter(
            uid=notification_uid,
            user=user
        ).update(is_read=True)

    @staticmethod
    def mark_all_as_read(user: User):
        return Notification.objects.filter(
            user=user,
            is_read=False
        ).update(is_read=True)