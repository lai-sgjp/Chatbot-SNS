import pytest
from unittest.mock import AsyncMock, Mock
from bot.models import Message
from bot.event_bus import EventBus, EventType
from bot.llm.base import BaseLLMEngine
from bot.personality.engine import PersonalityEngine
from bot.pipeline import MessagePipeline


@pytest.fixture
def mock_llm():
    engine = Mock(spec=BaseLLMEngine)
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
        user_name="测试用户",
        session_id="test_session",
    )
    reply = await pipeline.process(message)
    assert reply.text == "你好！我是助手。"
    mock_llm.chat.assert_awaited_once()


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
        text="测试事件",
        user_id="user1",
        user_name="测试用户",
        session_id="test_session",
    )
    await pipeline.process(message)
    assert events == ["pre", "post", "send"]


@pytest.mark.asyncio
async def test_pipeline_conversation_buffer(mock_llm, mock_personality, event_bus):
    pipeline = MessagePipeline(
        llm_engine=mock_llm,
        personality_engine=mock_personality,
        event_bus=event_bus,
    )
    msg1 = Message(text="第一轮", user_id="u1", user_name="u", session_id="s1")
    msg2 = Message(text="第二轮", user_id="u1", user_name="u", session_id="s1")
    await pipeline.process(msg1)
    await pipeline.process(msg2)
    buffer = pipeline._get_buffer("s1")
    assert len(buffer.get_messages()) == 4
