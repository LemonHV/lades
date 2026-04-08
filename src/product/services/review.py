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

    from django.db import transaction

    @transaction.atomic
    def create_review(self, user: User, payload: ReviewRequestSchema, files: list):
        product = self.product_orm.get_product_by_uid(uid=payload.product_uid)

        review = self.orm.create_review(
            user=user,
            product=product,
            rating=payload.rating,
            comment=payload.comment,
        )

        attachments = []

        for index, file in enumerate(files or []):
            attachment = self.attachment_service.upload_attachment(
                file=file,
                type=AttachmentType.REVIEW,
                public_id=f"review_{review.uid}_{index}",
                folder="review_images",
            )

            review_attachment = self.orm.create_review_attachment(
                review=review,
                attachment=attachment,
                sort_order=index,
                is_primary=(index == 0),
            )

            attachments.append(review_attachment)

        return review

    def get_reviews(self, uid: UUID):
        product = self.product_orm.get_product_by_uid(uid=uid)
        return self.orm.get_reviews(product=product)
