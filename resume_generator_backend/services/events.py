import asyncio
from typing import Callable, Any
from collections import defaultdict


class EventBus:
    """Async event bus backed by subscriber callbacks.

    ponytail: global single-instance bus, per-event subscriber lists if throughput matters.
    """

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable) -> None:
        self._subscribers[event].append(handler)

    def unsubscribe(self, event: str, handler: Callable) -> None:
        if handler in self._subscribers[event]:
            self._subscribers[event].remove(handler)

    async def publish(self, event: str, data: Any = None) -> None:
        for handler in self._subscribers.get(event, []):
            result = handler(data)
            if asyncio.iscoroutine(result):
                await result


bus = EventBus()
