from uuid import UUID

from cloudinary.uploader import destroy, upload

from attachment.exceptions import AttachmentNotExists, UploadAttachmentFail
from attachment.models import AttachmentType
from attachment.orm.attachment import AttachmentORM


class AttachmentService:
    def __init__(self):
        self.orm = AttachmentORM()

    def upload_attachment(
        self, file, folder: str, public_id: str, type: AttachmentType
    ):
        try:
            attachment_info = upload(
                file=file, folder=folder, public_id=public_id, overwrite=True
            )
        except Exception:
            raise UploadAttachmentFail

        url = attachment_info.get("secure_url")
        uploaded_public_id = attachment_info.get("public_id")

        if not url or not uploaded_public_id:
            raise UploadAttachmentFail

        return self.orm.save_attachment(
            url=url, public_id=uploaded_public_id, type=type
        )

    def delete_attachment(self, uid: UUID):
        attachment = self.orm.get_attachment_by_uid(uid=uid)

        if not attachment:
            raise AttachmentNotExists

        try:
            if attachment.public_id:
                destroy(attachment.public_id)
        except Exception:
            pass

        self.orm.delete_attachment(attachment=attachment)
