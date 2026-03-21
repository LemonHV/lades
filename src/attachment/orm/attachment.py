from uuid import UUID
from typing import Optional

from attachment.models import Attachment, AttachmentType


class AttachmentORM:
    @staticmethod
    def save_attachment(
        url: str,
        public_id: str,
        type: AttachmentType,
    ) -> Attachment:
        return Attachment.objects.create(
            url=url,
            public_id=public_id,
            type=type,
        )

    @staticmethod
    def get_attachment_by_uid(uid: UUID) -> Optional[Attachment]:
        return (
            Attachment.objects.filter(uid=uid)
            .only("uid", "url", "public_id", "type")
            .first()
        )

    @staticmethod
    def delete_attachment(attachment: Attachment) -> None:
        attachment.delete()
