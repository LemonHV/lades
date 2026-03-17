import logging
import time

from django.db import connection
from django.http import JsonResponse
from django.utils import timezone

LOGGER = logging.getLogger("django")


def get_client_ip(request):
    x_real_ip = request.META.get("HTTP_X_REAL_IP")
    if x_real_ip:
        return x_real_ip.strip()

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


class QueryCounter:
    def __init__(self):
        self.count = 0

    def __call__(self, execute, sql, params, many, context):
        self.count += 1
        return execute(sql, params, many, context)


class APIMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api"):
            return self.get_response(request)

        start = time.perf_counter()
        client_ip = get_client_ip(request)
        counter = QueryCounter()

        try:
            with connection.execute_wrapper(counter):
                response = self.get_response(request)
        except Exception:
            LOGGER.exception(
                "API Exception | method=%s path=%s ip=%s user=%s",
                request.method,
                request.path,
                client_ip,
                getattr(request, "user", None),
            )
            raise

        duration = time.perf_counter() - start

        LOGGER.info(
            "API Request | method=%s path=%s status=%s ip=%s user=%s duration=%.4fs queries=%s",
            request.method,
            request.path,
            response.status_code,
            client_ip,
            getattr(request, "user", None),
            duration,
            counter.count,
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