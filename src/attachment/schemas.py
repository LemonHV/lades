from ninja import ModelSchema
from pydantic import ConfigDict

from attachment.models import Attachment


class AttachmentSchema(ModelSchema):
    class Meta:
        model = Attachment
        exclude = ["public_id"]

    model_config = ConfigDict(from_attributes=True)
