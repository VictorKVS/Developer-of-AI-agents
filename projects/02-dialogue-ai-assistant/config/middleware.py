import logging
import time
import uuid

request_logger = logging.getLogger("mongoose.request")
error_logger = logging.getLogger("mongoose.error")


class RequestTracingMiddleware:
    """Log every HTTP request and attach a correlation ID."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            str(uuid.uuid4()),
        )
        request.correlation_id = correlation_id
        started_at = time.perf_counter()

        try:
            user = getattr(request, "user", None)
            username = getattr(user, "username", "anonymous") or "anonymous"

            request_logger.info(
                "REQUEST_START id=%s method=%s path=%s user=%s ip=%s",
                correlation_id,
                request.method,
                request.get_full_path(),
                username,
                self._get_client_ip(request),
            )

            response = self.get_response(request)
        except Exception:
            error_logger.exception(
                "REQUEST_EXCEPTION id=%s method=%s path=%s",
                correlation_id,
                request.method,
                request.get_full_path(),
            )
            raise

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        response["X-Correlation-ID"] = correlation_id

        logger = error_logger if response.status_code >= 400 else request_logger
        log_method = logger.error if response.status_code >= 400 else logger.info
        log_method(
            "REQUEST_END id=%s method=%s path=%s status=%s duration_ms=%s",
            correlation_id,
            request.method,
            request.get_full_path(),
            response.status_code,
            duration_ms,
        )

        return response

    @staticmethod
    def _get_client_ip(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
