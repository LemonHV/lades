from uuid import UUID
from product.schemas import ReviewRequestSchema
from product.orm.review import ReviewORM
from product.orm.product import ProductORM
from attachment.services import AttachmentService
from attachment.models import AttachmentType
from account.models import User


class ReviewService:
    def __init__(self) -> None:
        self.orm = ReviewORM()
        self.product_orm = ProductORM()
        self.attachment_service = AttachmentService()

    def create_review(self, user: User, payload: ReviewRequestSchema):
        product = self.product_orm.get_product_by_uid(uid=payload.product_uid)
        return self.orm.create_review(
            user=user, product=product, rating=payload.rating, comment=payload.comment
        )

    def create_review_attachments(self, uid: UUID, files: list):
        review = self.orm.get_review_by_uid(uid=uid)

        attachments = []

        for index, file in enumerate(files):
            attachment = self.attachment_service.upload_attachment(
                file=file,
                type=AttachmentType.REVIEW,
                public_id=f"review_{uid}_{index}",
                folder="review_images",
            )

            review_attachment = self.orm.create_review_attachment(
                review=review,
                attachment=attachment,
                sort_order=index,
                is_primary=(index == 0),
            )

            attachments.append(review_attachment)

        return attachments

    def get_reviews(self, uid: UUID):
        product = self.product_orm.get_product_by_uid(uid=uid)
        return self.orm.get_reviews(product=product)
