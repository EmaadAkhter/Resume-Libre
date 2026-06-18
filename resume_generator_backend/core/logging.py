import time
import logging
from datetime import datetime
from typing import Any, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from services.events import bus
from core.event_types import Events

logger = logging.getLogger("resume_libre")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


class EventLoggingSubscriber:
    """Subscribes to all pipeline events and logs them in a structured format.

    This is the debugging layer — every event that flows through the EventBus
    gets logged with a timestamp, making the full timeline visible.
    """

    _ALL_EVENTS = [
        Events.README_FETCHED,
        Events.PROMPT_BUILT,
        Events.LLM_GENERATING,
        Events.LLM_TOKEN,
        Events.LLM_COMPLETED,
        Events.VALIDATION_PASSED,
        Events.VALIDATION_FAILED,
        Events.API_REQUEST,
        Events.API_RESPONSE,
        Events.API_ERROR,
        Events.TEMPLATE_SELECTED,
        Events.TEMPLATE_UPLOADED,
        Events.RESUME_CREATED,
        Events.RESUME_DELETED,
        Events.VERSION_COMMITTED,
        Events.BRANCH_CREATED,
        Events.BRANCH_MERGED,
        Events.TAG_CREATED,
    ]

    @classmethod
    def register(cls, bus_instance):
        """Register logging handlers for all known events."""
        for event_name in cls._ALL_EVENTS:
            handler = cls._make_handler(event_name)
            bus_instance.subscribe(event_name, handler)

    @staticmethod
    def _make_handler(event_name: str) -> Callable:
        def handler(data: Any) -> None:
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            if isinstance(data, str):
                if len(data) > 80:
                    data_repr = data[:77] + "..."
                else:
                    data_repr = data
            elif isinstance(data, dict):
                safe = {}
                for k, v in data.items():
                    if isinstance(v, str) and len(v) > 60:
                        safe[k] = v[:57] + "..."
                    else:
                        safe[k] = v
                data_repr = safe
            else:
                data_repr = data

            logger.info(f"[{ts}] {event_name:30s} {data_repr}")

        return handler


class RequestResponseMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that emits api:request and api:response events.

    Gives you a timeline of every HTTP call with method, path, status, and duration.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip the debug SSE endpoint itself (would cause infinite self-logging noise)
        if request.url.path == "/debug/events":
            return await call_next(request)

        start = time.time()
        method = request.method
        path = request.url.path

        await bus.publish(
            Events.API_REQUEST,
            {"method": method, "path": path},
        )

        try:
            response = await call_next(request)
            duration_ms = int((time.time() - start) * 1000)

            await bus.publish(
                Events.API_RESPONSE,
                {
                    "method": method,
                    "path": path,
                    "status": response.status_code,
                    "ms": duration_ms,
                },
            )

            response.headers["X-Response-Time-ms"] = str(duration_ms)
            return response

        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            await bus.publish(
                Events.API_ERROR,
                {
                    "method": method,
                    "path": path,
                    "error": str(e)[:200],
                    "ms": duration_ms,
                },
            )
            raise
