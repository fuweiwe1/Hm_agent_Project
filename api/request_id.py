import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from utils.logger_handler import logger, request_id_var


class RequestIdMiddleware(BaseHTTPMiddleware):
    """为每个请求生成唯一 requestId，注入 contextvars 供全链路日志使用。"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 优先取上游传入的 X-Request-Id，否则生成
        req_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        request_id_var.set(req_id)

        start = time.perf_counter()
        logger.info(
            "request_start",
            extra={"method": request.method, "path": request.url.path},
        )

        response = await call_next(request)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info(
            "request_done",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "elapsed_ms": elapsed_ms,
            },
        )

        response.headers["X-Request-ID"] = req_id
        return response
