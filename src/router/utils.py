import logging
from typing import Union

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from ninja.constants import NOT_SET, NOT_SET_TYPE
from ninja.openapi.views import openapi_view
from ninja_extra import NinjaExtraAPI

from router.authenticate import AuthBear
from router.exception import generate_exception_response
from router.paginate import PaginatedResponseSchema


AuthType = Union[AuthBear, None, NOT_SET_TYPE]


logger = logging.getLogger("django")


def get_openapi_view(api: NinjaExtraAPI):
    @login_required
    def openapi_view_with_login_required(request: HttpRequest):
        return openapi_view(request, api)

    return openapi_view_with_login_required


def wrap_http_method(base_method):
    def wrapper(
        path: str,
        *,
        response=None,
        auth=NOT_SET,
        exceptions=(),
        paginate=False,
        **kwargs,
    ):
        final_auth: AuthType
        if auth is None:
            final_auth = None
        elif auth is NOT_SET:
            final_auth = NOT_SET
        elif auth:
            final_auth = AuthBear()
        else:
            final_auth = NOT_SET
        if paginate:
            return base_method(
                path,
                auth=final_auth,
                response=generate_exception_response(
                    PaginatedResponseSchema[response], *exceptions
                ),
                **kwargs,
            )
        return base_method(
            path,
            auth=final_auth,
            response=generate_exception_response(response, *exceptions),
            **kwargs,
        )

    return wrapper
