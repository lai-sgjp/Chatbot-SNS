import logging
from typing import Optional

from bot.llm.base import LLMMessage
from bot.pipeline import ConversationBuffer
from .long_term import LongTermMemory

logger = logging.getLogger(__name__)


class MemoryManager:
    """管理短期记忆 (Buffer) 和长期记忆 (ChromaDB) 的统一入口。

    职责：
    - 每个 session 独立的短期对话 Buffer
    - 长期记忆的自动存储与语义检索
    - 为用户消息拼接包含记忆的上下文
    """

    def __init__(
        self,
        short_term_size: int = 100,
        chroma_db_path: str = "data/chroma_db",
    ):
        self._short_term_size = short_term_size
        self._chroma_db_path = chroma_db_path
        self._buffers: dict[str, ConversationBuffer] = {}
        self.long_term = LongTermMemory(persist_directory=chroma_db_path)

    def _get_buffer(self, session_id: str) -> ConversationBuffer:
        if session_id not in self._buffers:
            self._buffers[session_id] = ConversationBuffer(self._short_term_size)
        return self._buffers[session_id]

    async def get_context(
        self,
        session_id: str,
        user_message: str,
        n_memories: int = 5,
    ) -> tuple[list[LLMMessage], list[dict]]:
        """获取当前会话的完整上下文：短期 + 长期记忆。"""
        buffer = self._get_buffer(session_id)
        # 查询长期记忆
        memories = await self.long_term.query_memories(
            query=user_message,
            n_results=n_memories,
            session_id=session_id,
        )
        context = list(buffer.get_messages())
        return context, memories

    async def store_interaction(
        self,
        session_id: str,
        user_msg: str,
        assistant_msg: str,
        user_id: str = "",
    ) -> None:
        """存储一轮对话到短期和长期记忆。"""
        buffer = self._get_buffer(session_id)
        buffer.add(LLMMessage(role="user", content=user_msg))
        buffer.add(LLMMessage(role="assistant", content=assistant_msg))
        # 同步到长期记忆
        await self.long_term.add_memory(
            session_id=session_id,
            user_id=user_id,
            content=f"用户: {user_msg}\n助手: {assistant_msg}",
            memory_type="conversation",
        )

    def get_short_term_messages(self, session_id: str) -> list[LLMMessage]:
        """获取短期记忆消息列表。"""
        return list(self._get_buffer(session_id).get_messages())

    async def clear_session(self, session_id: str) -> None:
        """清除会话的所有记忆（短期 + 长期）。"""
        if session_id in self._buffers:
            del self._buffers[session_id]
        await self.long_term.clear_session(session_id)
