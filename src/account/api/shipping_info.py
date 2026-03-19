from typing import List
from uuid import UUID

from account.schemas.account import MessageResponseSchema
from account.schemas.shipping_info import (
    ShippingInfoCreateSchema,
    ShippingInfoResponseSchema,
    ShippingInfoUpdateSchema,
)
from account.services.shipping_info import ShippingInfoService
from account.utils import SuccessMessage
from router.authenticate import AuthBear
from router.controller import Controller, api, delete, get, post, put
from router.types import AuthenticatedRequest


@api(prefix_or_class="shipping-infos", tags=["ShippingInfo"], auth=None)
class ShippingInfoAPI(Controller):
    def __init__(self, service: ShippingInfoService):
        self.service = service

    @post(
        "",
        auth=AuthBear(),
        response=ShippingInfoResponseSchema,
    )
    def add_shipping_info(
        self,
        request: AuthenticatedRequest,
        payload: ShippingInfoCreateSchema,
    ):
        return self.service.add_shipping_info(
            user=request.user,
            payload=payload,
        )

    @get(
        "",
        auth=AuthBear(),
        response=List[ShippingInfoResponseSchema],
    )
    def get_shipping_infos(self, request: AuthenticatedRequest):
        return self.service.get_shipping_infos(user=request.user)

    @get(
        "/{uid}",
        response=ShippingInfoResponseSchema,
        auth=AuthBear(),
    )
    def get_shipping_info_detail(
        self,
        request: AuthenticatedRequest,
        uid: UUID,
    ):
        return self.service.get_shipping_info_detail(
            user=request.user,
            shipping_info_uid=uid,
        )

    @put(
        "/{uid}",
        response=ShippingInfoResponseSchema,
        auth=AuthBear(),
    )
    def update_shipping_info(
        self,
        request: AuthenticatedRequest,
        uid: UUID,
        payload: ShippingInfoUpdateSchema,
    ):
        return self.service.update_shipping_info(
            user=request.user,
            shipping_info_uid=uid,
            payload=payload,
        )

    @delete(
        "/{uid}",
        response=MessageResponseSchema,
        auth=AuthBear(),
    )
    def delete_shipping_info(
        self,
        request: AuthenticatedRequest,
        uid: UUID,
    ):
        self.service.delete_shipping_info(
            user=request.user,
            shipping_info_uid=uid,
        )
        return MessageResponseSchema(message=SuccessMessage.SHIPPING_INFO_DELETED)

    @put(
        "/{uid}/set-default",
        response=MessageResponseSchema,
        auth=AuthBear(),
    )
    def set_default_shipping_info(
        self,
        request: AuthenticatedRequest,
        uid: UUID,
    ):
        self.service.set_default_shipping_info(
            user=request.user,
            shipping_info_uid=uid,
        )
        return MessageResponseSchema(message=SuccessMessage.DEFAULT_SHIPPING_INFO_SET)
