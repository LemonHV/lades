from account.models import User
from product.models import Product, Review, ReviewAttachment
from attachment.models import Attachment
from uuid import UUID
from django.db.models import Prefetch

class ReviewORM:
    @staticmethod
    def create_review(
        user: User, product: Product, rating: int, comment: str = ""
    ) -> Review:
        return Review.objects.create(
            user=user,
            product=product,
            rating=rating,
            comment=comment,
        )

    @staticmethod
    def get_review_by_uid(uid: UUID) -> Review:
        return Review.objects.get(uid=uid)

    @staticmethod
    def create_review_attachment(review: Review, attachment: Attachment):
        return ReviewAttachment.objects.create(
            review=review,
            attachment=attachment,
        )

    @staticmethod
    def get_reviews(product: Product):
        return (
            Review.objects.filter(product=product)
            .select_related("user")
            .prefetch_related(
                Prefetch(
                    "review_attachments",
                    queryset=ReviewAttachment.objects.select_related("attachment"),
                    to_attr="images",
                )
            )
            .order_by("-created_at")
        )
