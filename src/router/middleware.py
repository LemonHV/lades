import logging
import time

from django.http import JsonResponse
from django.utils import timezone

LOGGER = logging.getLogger("django")


class APIMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api"):
            return self.get_response(request)

        started_time = time.perf_counter()

        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")

        try:
            response = self.get_response(request)
        except Exception:
            LOGGER.exception(
                "---------------------------------------------------------------\n"
                f"> Method: {request.method}\n"
                f"> Path: {request.path}\n"
                f"> IP Address: {ip_address}\n"
                f"> Authenticator: {getattr(request, 'user', None)}\n"
                "---------------------------------------------------------------"
            )
            raise

        ended_time = time.perf_counter()

        LOGGER.info(
            "---------------------------------------------------------------\n"
            f"> Method: {request.method}\n"
            f"> Path: {request.path}\n"
            f"> Response: {response.status_code}\n"
            f"> IP Address: {ip_address}\n"
            f"> Authenticator: {getattr(request, 'user', None)}\n"
            f"> Running time: {ended_time - started_time:.4f}s\n"
            "---------------------------------------------------------------"
        )

        if response.status_code == 404:
            return JsonResponse(
                {
                    "data": None,
                    "error_code": 404,
                    "message_code": "PAGE_NOT_FOUND",
                    "message": "Page not found",
                    "current_time": timezone.now(),
                },
                status=404,
            )

        return response
