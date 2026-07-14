from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    text: str | None
    user_id: str
    user_name: str
    session_id: str
    is_voice: bool = False
    raw: Any = None


@dataclass
class Reply:
    text: str | None = None
    voice: bytes | None = None


@dataclass
class LLMMessage:
    role: str
    content: str
