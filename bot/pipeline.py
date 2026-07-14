import logging

from .models import Message, Reply
from .event_bus import EventBus, EventType
from .llm.base import BaseLLMEngine, LLMMessage
from .personality.engine import PersonalityEngine

logger = logging.getLogger(__name__)


class ConversationBuffer:
    """短期对话消息缓冲区（FIFO 滑动窗口）。"""

    def __init__(self, max_size: int = 100):
        self._messages: list[LLMMessage] = []
        self._max_size = max_size

    def add(self, message: LLMMessage):
        self._messages.append(message)
        if len(self._messages) > self._max_size:
            self._messages.pop(0)

    def get_messages(self) -> list[LLMMessage]:
        return list(self._messages)


class MessagePipeline:
    """消息处理管道：人格注入 -> 记忆检索 -> LLM 调用 -> 记忆存储。"""

    def __init__(
        self,
        llm_engine: BaseLLMEngine,
        personality_engine: PersonalityEngine,
        event_bus: EventBus,
        memory_manager=None,
    ):
        self._llm = llm_engine
        self._personality = personality_engine
        self._event_bus = event_bus
        self._memory = memory_manager

    async def process(self, message: Message) -> Reply:
        await self._event_bus.publish(EventType.MESSAGE_PRE_PROCESS, message=message)

        # 查询长期记忆并注入上下文
        system_prompt = self._personality.build_system_prompt()

        # 存储到记忆系统
        if self._memory:
            context_messages, memories = await self._memory.get_context(
                message.session_id, message.text or ""
            )
            if memories:
                memory_lines = []
                for m in memories[:3]:
                    mtype = m["metadata"].get("type", "记忆")
                    content = m["content"][:200]
                    memory_lines.append(f"- [{mtype}] {content}")
                system_prompt += (
                    "\n\n## ??????\n" + "\n".join(memory_lines)
                )
        else:
            context_messages = []

        # ?? LLM ??
        llm_messages = [LLMMessage(role="system", content=system_prompt)]
        if context_messages:
            llm_messages.extend(context_messages)
        llm_messages.append(
            LLMMessage(role="user", content=message.text or "")
        )

        # LLM ??
        reply_text = await self._llm.chat(llm_messages)

        # ???????
        if self._memory:
            await self._memory.store_interaction(
                message.session_id,
                message.text or "",
                reply_text,
                user_id=message.user_id,
            )

        reply = Reply(text=reply_text)
        await self._event_bus.publish(
            EventType.MESSAGE_POST_PROCESS, message=message, reply=reply
        )
        await self._event_bus.publish(EventType.REPLY_PRE_SEND, reply=reply)
        return reply

