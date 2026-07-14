import logging
from openai import AsyncOpenAI

from .base import BaseLLMEngine, LLMMessage

logger = logging.getLogger(__name__)


class OpenAIEngine(BaseLLMEngine):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=openai_messages,
            temperature=temperature if temperature is not None else self._temperature,
            max_tokens=max_tokens if max_tokens is not None else self._max_tokens,
        )

        content = resp.choices[0].message.content or ""
        logger.debug("LLM response: %s", content[:100])
        return content
