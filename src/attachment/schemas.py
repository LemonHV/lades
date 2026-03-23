from ninja import ModelSchema
from attachment.models import Attachment
from pydantic import ConfigDict


class AttachmentSchema(ModelSchema):
    class Meta:
        model = Attachment
        exclude = ["public_id"]

    model_config = ConfigDict(from_attributes=True)
