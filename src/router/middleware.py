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


def get_user_display(request):
    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False):
        return (
            getattr(user, "email", None) or getattr(user, "username", None) or str(user)
        )
    return "Anonymous"


def error_response(
    *,
    error_code,
    message_code,
    message,
    status,
    data=None,
):
    return JsonResponse(
        {
            "data": data,
            "error_code": error_code,
            "message_code": message_code,
            "message": message,
            "current_time": timezone.now().isoformat(),
        },
        status=status,
    )


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

        start_time = time.perf_counter()
        client_ip = get_client_ip(request)
        counter = QueryCounter()

        user_display = "anon"

        try:
            with connection.execute_wrapper(counter):
                response = self.get_response(request)

            user_display = get_user_display(request)

        except Exception:
            duration = time.perf_counter() - start_time
            duration_ms = int(duration * 1000)

            try:
                user_display = get_user_display(request)
            except Exception:
                pass

            LOGGER.exception(
                "❌ [%s] %s %s | %dms | q=%s | user=%s | ip=%s",
                500,
                request.method,
                request.path,
                duration_ms,
                counter.count,
                user_display,
                client_ip,
            )
            raise

        duration = time.perf_counter() - start_time
        duration_ms = int(duration * 1000)
        status_code = int(response.status_code)
        log_msg = "[%s] %s %s | %dms | q=%s | user=%s | ip=%s"

        LOGGER.info(
            log_msg,
            status_code,
            request.method,
            request.path,
            duration_ms,
            counter.count,
            user_display,
            client_ip,
        )

        if duration > 1:
            LOGGER.warning(
                "🐢 " + log_msg,
                status_code,
                request.method,
                request.path,
                duration_ms,
                counter.count,
                user_display,
                client_ip,
            )

        if status_code == 404:
            return error_response(
                error_code=404,
                message_code="PAGE_NOT_FOUND",
                message="Page not found",
                status=404,
            )

        return response
