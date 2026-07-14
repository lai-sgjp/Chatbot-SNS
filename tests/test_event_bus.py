import pytest
from bot.event_bus import EventBus, EventType


@pytest.mark.asyncio
async def test_subscribe_and_publish():
    bus = EventBus()
    results = []

    async def handler(**kwargs):
        results.append(kwargs.get("value"))

    bus.subscribe(EventType.MESSAGE_PRE_PROCESS, handler)
    await bus.publish(EventType.MESSAGE_PRE_PROCESS, value=42)
    assert results == [42]


@pytest.mark.asyncio
async def test_multiple_handlers():
    bus = EventBus()
    results = []

    async def handler1(**kwargs):
        results.append("h1")

    async def handler2(**kwargs):
        results.append("h2")

    bus.subscribe(EventType.MESSAGE_PRE_PROCESS, handler1)
    bus.subscribe(EventType.MESSAGE_PRE_PROCESS, handler2)
    await bus.publish(EventType.MESSAGE_PRE_PROCESS)
    assert results == ["h1", "h2"]


@pytest.mark.asyncio
async def test_unsubscribe():
    bus = EventBus()
    results = []

    async def handler(**kwargs):
        results.append("called")

    bus.subscribe(EventType.MESSAGE_PRE_PROCESS, handler)
    bus.unsubscribe(EventType.MESSAGE_PRE_PROCESS, handler)
    await bus.publish(EventType.MESSAGE_PRE_PROCESS)
    assert results == []


@pytest.mark.asyncio
async def test_no_handlers():
    bus = EventBus()
    await bus.publish(EventType.MESSAGE_PRE_PROCESS)
