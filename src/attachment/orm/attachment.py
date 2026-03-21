from attachment.models import Attachment
from uuid import UUID


class AttachmentORM:
    @staticmethod
    def save_attachment(url: str, public_id: str) -> Attachment:
        return Attachment.objects.create(url=url, public_id=public_id)

    @staticmethod
    def get_attachment_by_uid(uid: UUID):
        return Attachment.objects.filter(uid=uid).first()

    @staticmethod
    def delete_attachment(attachment: Attachment):
        attachment.delete()
