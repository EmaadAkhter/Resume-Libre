import asyncio
import json
from datetime import datetime
from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from services.events import bus, EventBus
from core.event_types import Events

router = APIRouter(prefix="/debug", tags=["debug"])


class DebugEventRelay:
    """Relays all bus events to a queue for SSE streaming.

    Each SSE client gets its own queue. Events are pushed to all active queues.
    ponytail: per-client asyncio.Queue, fine for a handful of debug clients.
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

    def __init__(self, bus_instance: EventBus):
        self.bus = bus_instance
        self._queues: list[asyncio.Queue] = []
        self._handlers: dict[asyncio.Queue, Callable] = {}

    def add_client(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        def make_handler(q: asyncio.Queue, event_name: str) -> Callable:
            def handler(data: Any) -> None:
                try:
                    q.put_nowait(
                        {
                            "event": event_name,
                            "data": _truncate(data),
                            "ts": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                        }
                    )
                except asyncio.QueueFull:
                    pass

            return handler

        handlers = {}
        for event_name in self._ALL_EVENTS:
            h = make_handler(queue, event_name)
            self.bus.subscribe(event_name, h)
            handlers[event_name] = h

        self._queues.append(queue)
        self._handlers[queue] = handlers
        return queue

    def remove_client(self, queue: asyncio.Queue) -> None:
        handlers = self._handlers.pop(queue, {})
        for event_name, h in handlers.items():
            self.bus.unsubscribe(event_name, h)
        if queue in self._queues:
            self._queues.remove(queue)


def _truncate(data: Any) -> Any:
    if isinstance(data, str):
        return data[:200] + "..." if len(data) > 200 else data
    if isinstance(data, dict):
        return {
            k: (v[:100] + "..." if isinstance(v, str) and len(v) > 100 else v)
            for k, v in data.items()
        }
    return data


_relay = DebugEventRelay(bus)


@router.get("/events")
async def debug_events():
    """Live SSE stream of all internal EventBus events.

    Open http://localhost:8000/debug/events in a browser tab while using the app
    to see the full event timeline in real-time.
    """
    queue = _relay.add_client()

    async def event_stream():
        try:
            # Send a welcome event so the client knows it's connected
            yield f"data: {json.dumps({'event': 'debug:connected', 'ts': datetime.now().strftime('%H:%M:%S')})}\n\n"

            while True:
                try:
                    event_data = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(event_data)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive comment
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            _relay.remove_client(queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
