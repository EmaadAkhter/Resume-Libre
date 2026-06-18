import asyncio
from services.events import EventBus


def test_event_bus_subscribe_and_publish():
    bus = EventBus()
    received = []

    bus.subscribe("test:event", lambda data: received.append(data))
    asyncio.run(bus.publish("test:event", "hello"))

    assert received == ["hello"]


def test_event_bus_multiple_subscribers():
    bus = EventBus()
    results = []

    bus.subscribe("test:event", lambda data: results.append(f"a:{data}"))
    bus.subscribe("test:event", lambda data: results.append(f"b:{data}"))
    asyncio.run(bus.publish("test:event", "msg"))

    assert "a:msg" in results
    assert "b:msg" in results


def test_event_bus_no_subscribers():
    bus = EventBus()
    # Should not raise
    asyncio.run(bus.publish("unhandled:event", "data"))


def test_event_bus_unsubscribe():
    bus = EventBus()
    received = []

    def handler(data):
        received.append(data)
    bus.subscribe("test:event", handler)
    bus.unsubscribe("test:event", handler)
    asyncio.run(bus.publish("test:event", "hello"))

    assert received == []


def test_event_bus_async_handler():
    bus = EventBus()
    received = []

    async def async_handler(data):
        received.append(data)

    bus.subscribe("test:async", async_handler)
    asyncio.run(bus.publish("test:async", "async-data"))

    assert received == ["async-data"]
