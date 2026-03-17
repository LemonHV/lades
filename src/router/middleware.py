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
            "current_time": timezone.now().isoformat(),  # fix serialize
        },
        status=status,
    )


class APIMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # chỉ apply cho API
        if not request.path.startswith("/api"):
            return self.get_response(request)

        start_time = time.perf_counter()
        client_ip = get_client_ip(request)
        counter = QueryCounter()

        try:
            with connection.execute_wrapper(counter):
                response = self.get_response(request)

        except Exception:
            LOGGER.exception(
                "\n"
                "❌ API EXCEPTION\n"
                "Method : %s\n"
                "Path   : %s\n"
                "IP     : %s\n"
                "User   : %s\n"
                "----------------------------------------",
                request.method,
                request.path,
                client_ip,
                getattr(request, "user", None),
            )
            raise

        duration = time.perf_counter() - start_time

        # log đẹp nhiều dòng
        LOGGER.info(
            "\n"
            "🚀 API REQUEST\n"
            "----------------------------------------\n"
            "Method     : %s\n"
            "Path       : %s\n"
            "Status     : %s\n"
            "IP         : %s\n"
            "User       : %s\n"
            "Duration   : %.4fs\n"
            "Queries    : %s\n"
            "----------------------------------------",
            request.method,
            request.path,
            response.status_code,
            client_ip,
            getattr(request, "user", None),
            duration,
            counter.count,
        )

        # format error chuẩn
        if response.status_code == 404:
            return error_response(
                error_code=404,
                message_code="PAGE_NOT_FOUND",
                message="Page not found",
                status=404,
            )

        return response