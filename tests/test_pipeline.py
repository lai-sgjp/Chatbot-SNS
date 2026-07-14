import pytest
from unittest.mock import AsyncMock, Mock
from bot.models import Message
from bot.event_bus import EventBus, EventType
from bot.llm.base import BaseLLMEngine
from bot.personality.engine import PersonalityEngine
from bot.pipeline import MessagePipeline


@pytest.fixture
def mock_llm():
    engine = AsyncMock(spec=BaseLLMEngine)
    engine.chat = AsyncMock(return_value="你好！我是助手。")
    return engine


@pytest.fixture
def mock_personality():
    engine = Mock(spec=PersonalityEngine)
    engine.build_system_prompt = Mock(return_value="你是助手")
    return engine


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.mark.asyncio
async def test_pipeline_process(mock_llm, mock_personality, event_bus):
    pipeline = MessagePipeline(
        llm_engine=mock_llm,
        personality_engine=mock_personality,
        event_bus=event_bus,
    )
    message = Message(
        text="你好",
        user_id="user1",
        user_name="你是助手",
        session_id="test_session",
    )
    reply = await pipeline.process(message)
    assert reply.text == "你好！我是助手。"
    mock_llm.chat.assert_awaited_once()
    mock_personality.build_system_prompt.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_event_hooks(mock_llm, mock_personality, event_bus):
    events = []

    async def pre_process(**kwargs):
        events.append("pre")

    async def post_process(**kwargs):
        events.append("post")

    async def pre_send(**kwargs):
        events.append("send")

    event_bus.subscribe(EventType.MESSAGE_PRE_PROCESS, pre_process)
    event_bus.subscribe(EventType.MESSAGE_POST_PROCESS, post_process)
    event_bus.subscribe(EventType.REPLY_PRE_SEND, pre_send)

    pipeline = MessagePipeline(
        llm_engine=mock_llm,
        personality_engine=mock_personality,
        event_bus=event_bus,
    )
    message = Message(
        text="你是助手",
        user_id="user1",
        user_name="你是助手",
        session_id="test_session",
    )
    await pipeline.process(message)
    assert events == ["pre", "post", "send"]


@pytest.mark.asyncio
async def test_pipeline_with_memory(mock_llm, mock_personality, event_bus):
    from bot.memory.manager import MemoryManager

    mm = MemoryManager(short_term_size=10)
    await mm.store_interaction("s1", "???", "??1")
    await mm.store_interaction("s1", "???", "??2")

    pipeline = MessagePipeline(
        llm_engine=mock_llm,
        personality_engine=mock_personality,
        event_bus=event_bus,
        memory_manager=mm,
    )
    msg = Message(text="你好", user_id="u1", user_name="u", session_id="s1")
    reply = await pipeline.process(msg)
    assert reply.text == "你好！我是助手。"

    context, memories = await mm.get_context("s1", "??")
    assert len(context) == 6

