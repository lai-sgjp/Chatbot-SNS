import logging

from .models import Message, Reply
from .event_bus import EventBus, EventType
from .llm.base import BaseLLMEngine, LLMMessage
from .personality.engine import PersonalityEngine

logger = logging.getLogger(__name__)


class ConversationBuffer:
    def __init__(self, max_size: int = 20):
        self._messages: list[LLMMessage] = []
        self._max_size = max_size

    def add(self, message: LLMMessage):
        self._messages.append(message)
        if len(self._messages) > self._max_size:
            self._messages.pop(0)

    def get_messages(self) -> list[LLMMessage]:
        return list(self._messages)


class MessagePipeline:
    def __init__(
        self,
        llm_engine: BaseLLMEngine,
        personality_engine: PersonalityEngine,
        event_bus: EventBus,
        short_term_size: int = 20,
    ):
        self._llm = llm_engine
        self._personality = personality_engine
        self._event_bus = event_bus
        self._buffers: dict[str, ConversationBuffer] = {}
        self._short_term_size = short_term_size

    def _get_buffer(self, session_id: str) -> ConversationBuffer:
        if session_id not in self._buffers:
            self._buffers[session_id] = ConversationBuffer(self._short_term_size)
        return self._buffers[session_id]

    async def process(self, message: Message) -> Reply:
        await self._event_bus.publish(EventType.MESSAGE_PRE_PROCESS, message=message)

        system_prompt = self._personality.build_system_prompt()

        buffer = self._get_buffer(message.session_id)
        llm_messages = [LLMMessage(role="system", content=system_prompt)]
        llm_messages.extend(buffer.get_messages())
        llm_messages.append(LLMMessage(role="user", content=message.text or ""))

        reply_text = await self._llm.chat(llm_messages)

        buffer.add(LLMMessage(role="user", content=message.text or ""))
        buffer.add(LLMMessage(role="assistant", content=reply_text))

        reply = Reply(text=reply_text)
        await self._event_bus.publish(EventType.MESSAGE_POST_PROCESS, message=message, reply=reply)
        await self._event_bus.publish(EventType.REPLY_PRE_SEND, reply=reply)

        return reply
