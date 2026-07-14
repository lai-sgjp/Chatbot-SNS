import pytest
from bot.memory.manager import MemoryManager


@pytest.mark.asyncio
async def test_memory_manager_store_and_context():
    mm = MemoryManager(short_term_size=10)
    await mm.store_interaction("s1", "你好", "你好！有什么可以帮助你的吗？")
    await mm.store_interaction("s1", "今天天气怎么样？", "今天天气很好。")

    context, memories = await mm.get_context("s1", "你好")
    assert len(context) == 4
    assert context[0].role == "user"
    assert context[0].content == "你好"


@pytest.mark.asyncio
async def test_memory_manager_separate_sessions():
    mm = MemoryManager(short_term_size=100)
    await mm.store_interaction("s1", "消息1", "消息1")
    await mm.store_interaction("s2", "消息2", "消息2")

    ctx1, _ = await mm.get_context("s1", "消息1")
    ctx2, _ = await mm.get_context("s2", "消息2")

    assert len(ctx1) == 2
    assert len(ctx2) == 2
    assert ctx1[0].content == "消息1"


@pytest.mark.asyncio
async def test_memory_manager_clear():
    mm = MemoryManager(short_term_size=10)
    await mm.store_interaction("s1", "你好", "你好")
    await mm.clear_session("s1")
    ctx, _ = await mm.get_context("s1", "你好")
    assert len(ctx) == 0


