from enum import StrEnum, auto
from typing import Callable, Awaitable
import logging

logger = logging.getLogger(__name__)

Handler = Callable[..., Awaitable[None]]


class EventType(StrEnum):
    MESSAGE_PRE_PROCESS = auto()
    MESSAGE_POST_PROCESS = auto()
    REPLY_PRE_SEND = auto()


class EventBus:
    def __init__(self):
        self._handlers: dict[EventType, list[Handler]] = {}

    def subscribe(self, event_type: EventType, handler: Handler):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug("Handler %s subscribed to %s", handler.__name__, event_type)

    def unsubscribe(self, event_type: EventType, handler: Handler):
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    async def publish(self, event_type: EventType, **kwargs):
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(**kwargs)
            except Exception as e:
                logger.exception(
                    "Handler %s failed for event %s: %s",
                    handler.__name__, event_type, e,
                )
