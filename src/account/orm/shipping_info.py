from typing import Optional
from uuid import UUID

from django.db import transaction
from django.utils.timezone import now

from account.models import ShippingInfo, User


class ShippingInfoORM:
    @staticmethod
    def get_shipping_infos(user: User):
        return ShippingInfo.objects.filter(user=user).order_by(
            "-is_default", "-created_at"
        )

    @staticmethod
    def get_shipping_info_by_uid(uid: UUID) -> Optional[ShippingInfo]:
        return ShippingInfo.objects.select_related("user").filter(uid=uid).first()

    @staticmethod
    def get_user_shipping_info_by_uid(user: User, uid: UUID) -> Optional[ShippingInfo]:
        return ShippingInfo.objects.filter(user=user, uid=uid).first()

    @staticmethod
    def create_shipping_info(user: User, **fields) -> ShippingInfo:
        shipping_info = ShippingInfo(user=user, **fields)
        shipping_info.save()
        return shipping_info

    @staticmethod
    def update_shipping_info(shipping_info: ShippingInfo, **fields) -> ShippingInfo:
        updated_fields: list[str] = []

        for key, value in fields.items():
            if value is None or not hasattr(shipping_info, key):
                continue

            if isinstance(value, str):
                value = value.strip()

            if getattr(shipping_info, key) != value:
                setattr(shipping_info, key, value)
                updated_fields.append(key)

        if updated_fields:
            updated_fields.append("updated_at")
            shipping_info.save(update_fields=updated_fields)

        return shipping_info

    @staticmethod
    def delete_shipping_info(shipping_info: ShippingInfo) -> None:
        shipping_info.delete()

    @staticmethod
    @transaction.atomic
    def set_default_shipping_info(
        user: User, shipping_info: ShippingInfo
    ) -> ShippingInfo:
        ShippingInfo.objects.filter(user=user, is_default=True).exclude(
            uid=shipping_info.uid
        ).update(
            is_default=False,
            updated_at=now(),
        )

        if not shipping_info.is_default:
            shipping_info.is_default = True
            shipping_info.save(update_fields=["is_default", "updated_at"])

        return shipping_info
