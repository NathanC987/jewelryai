import json
import logging
import sys
import time
from typing import Callable
from uuid import uuid4

from fastapi import Request, Response

from app.core.config import settings


def configure_logging() -> None:
    """Configure simple JSON logging for consistent service-level observability."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(message)s", stream=sys.stdout)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(payload)


def configure_json_formatter() -> None:
    for handler in logging.getLogger().handlers:
        handler.setFormatter(JsonFormatter())


async def request_logging_middleware(request: Request, call_next: Callable) -> Response:
    logger = logging.getLogger("api.request")
    request_id = request.headers.get("x-request-id", str(uuid4()))
    start = time.perf_counter()

    response = None
    status = "success"
    try:
        response = await call_next(request)
        return response
    except Exception:
        status = "error"
        raise
    finally:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "operation": f"{request.method} {request.url.path}",
                    "elapsed_ms": elapsed_ms,
                    "status": status,
                    "http_status": getattr(response, "status_code", 500),
                }
            )
        )
