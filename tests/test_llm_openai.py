import pytest
from bot.llm.openai_engine import OpenAIEngine


def test_engine_initialization():
    engine = OpenAIEngine(
        api_key="sk-test",
        base_url="https://api.openai.com/v1",
        model="gpt-4o",
    )
    assert engine._model == "gpt-4o"
    assert engine._temperature == 0.7


@pytest.mark.skip(reason="需要真实的 API 端点")
@pytest.mark.asyncio
async def test_chat_real():
    engine = OpenAIEngine(
        api_key="your-api-key",
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
    )
    from bot.llm.base import LLMMessage
    messages = [
        LLMMessage(role="system", content="你是一个助手"),
        LLMMessage(role="user", content="说你好"),
    ]
    response = await engine.chat(messages)
    assert isinstance(response, str)
    assert len(response) > 0
