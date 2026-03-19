from uuid import UUID

from account.exceptions import ShippingInfoNotFound
from account.models import User
from account.orm.shipping_info import ShippingInfoORM
from account.schemas.shipping_info import (
    ShippingInfoCreateSchema,
    ShippingInfoUpdateSchema,
)


class ShippingInfoService:
    def __init__(self):
        self.orm = ShippingInfoORM()

    def add_shipping_info(
        self,
        user: User,
        payload: ShippingInfoCreateSchema,
    ):
        data = payload.model_dump(exclude_unset=True)

        has_shipping_info = self.orm.get_shipping_infos(user=user).exists()
        requested_default = data.pop("is_default", False)

        should_set_default = requested_default or not has_shipping_info

        shipping_info = self.orm.create_shipping_info(
            user=user,
            **data,
            is_default=False,
        )

        if should_set_default:
            shipping_info = self.orm.set_default_shipping_info(
                user=user,
                shipping_info=shipping_info,
            )

        return shipping_info

    def get_shipping_infos(self, user: User):
        return self.orm.get_shipping_infos(user=user)

    def get_shipping_info_detail(
        self,
        user: User,
        shipping_info_uid: UUID,
    ):
        shipping_info = self.orm.get_user_shipping_info_by_uid(
            user=user,
            uid=shipping_info_uid,
        )
        if not shipping_info:
            raise ShippingInfoNotFound
        return shipping_info

    def update_shipping_info(
        self,
        user: User,
        shipping_info_uid: UUID,
        payload: ShippingInfoUpdateSchema,
    ):
        shipping_info = self.orm.get_user_shipping_info_by_uid(
            user=user,
            uid=shipping_info_uid,
        )
        if not shipping_info:
            raise ShippingInfoNotFound

        data = payload.model_dump(exclude_unset=True)

        shipping_info = self.orm.update_shipping_info(
            shipping_info=shipping_info,
            **data,
        )

        if data.get("is_default") is True:
            shipping_info = self.orm.set_default_shipping_info(
                user=user,
                shipping_info=shipping_info,
            )

        return shipping_info

    def delete_shipping_info(
        self,
        user: User,
        shipping_info_uid: UUID,
    ) -> None:
        shipping_info = self.orm.get_user_shipping_info_by_uid(
            user=user,
            uid=shipping_info_uid,
        )
        if not shipping_info:
            raise ShippingInfoNotFound

        was_default = shipping_info.is_default
        self.orm.delete_shipping_info(shipping_info=shipping_info)

        if was_default:
            next_shipping_info = self.orm.get_shipping_infos(user=user).first()
            if next_shipping_info:
                self.orm.set_default_shipping_info(
                    user=user,
                    shipping_info=next_shipping_info,
                )

    def set_default_shipping_info(
        self,
        user: User,
        shipping_info_uid: UUID,
    ):
        shipping_info = self.orm.get_user_shipping_info_by_uid(
            user=user,
            uid=shipping_info_uid,
        )
        if not shipping_info:
            raise ShippingInfoNotFound

        return self.orm.set_default_shipping_info(
            user=user,
            shipping_info=shipping_info,
        )
