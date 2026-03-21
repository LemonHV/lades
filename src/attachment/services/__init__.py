from attachment.orm.attachment import AttachmentORM
from cloudinary.uploader import upload, destroy
from attachment.exceptions import UploadAttachmentFail, AttachmentNotExists
from uuid import UUID


class AttachmentService:
    def __init__(self):
        self.orm = AttachmentORM()

    def upload_attachment(self, file, folder: str, public_id: str):
        attachment_info = upload(
            file=file,
            folder=folder,
            public_id=public_id,
            overwrite=True,
        )

        url = attachment_info.get("secure_url")
        uploaded_public_id = attachment_info.get("public_id")

        if not url or not uploaded_public_id:
            raise UploadAttachmentFail

        attachment = self.orm.save_attachment(
            url=url,
            public_id=uploaded_public_id,
        )
        return attachment

    def delete_attachment(self, uid: UUID):
        attachment = self.orm.get_attachment_by_uid(uid=uid)

        if not attachment:
            raise AttachmentNotExists

        if attachment.public_id:
            destroy(attachment.public_id)

        self.orm.delete_attachment(attachment=attachment)
