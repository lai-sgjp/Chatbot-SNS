from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
import yaml
from pathlib import Path


class LLMConfig(BaseModel):
    provider: str = "openai"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 8192


class PersonalityConfig(BaseModel):
    card_dir: str = "bot/personality/cards"
    default_card: str = "default"


class MemoryConfig(BaseModel):
    short_term_size: int = 100
    chroma_db_path: str = "data/chroma_db"


class AdapterConfig(BaseModel):
    adapter: str = "terminal"


class BotConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BOT_")

    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 8192

    personality_card_dir: str = "bot/personality/cards"
    personality_default_card: str = "default"

    memory_short_term_size: int = 100
    memory_chroma_db_path: str = "data/chroma_db"

    adapter_adapter: str = "terminal"

    # === QQ 适配器配置 ===
    qq_ws_url: str = "ws://localhost:8080"
    qq_token: str = ""

    # === 语音配置 ===
    voice_enabled: bool = False
    voice_edge_voice: str = "zh-CN-XiaoxiaoNeural"
    voice_edge_rate: str = "+0%"
    voice_edge_volume: str = "+0%"

    debug: bool = False

    @property
    def llm(self) -> LLMConfig:
        return LLMConfig(
            provider=self.llm_provider,
            api_key=self.llm_api_key,
            base_url=self.llm_base_url,
            model=self.llm_model,
            temperature=self.llm_temperature,
            max_tokens=self.llm_max_tokens,
        )

    @property
    def personality(self) -> PersonalityConfig:
        return PersonalityConfig(
            card_dir=self.personality_card_dir,
            default_card=self.personality_default_card,
        )

    @property
    def memory(self) -> MemoryConfig:
        return MemoryConfig(
            short_term_size=self.memory_short_term_size,
            chroma_db_path=self.memory_chroma_db_path,
        )

    @property
    def adapter(self) -> AdapterConfig:
        return AdapterConfig(adapter=self.adapter_adapter)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "BotConfig":
        path = Path(path)
        if not path.exists():
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        flat = {}
        for section in ("llm", "personality", "memory", "adapter"):
            section_data = data.get(section, {})
            for key, value in section_data.items():
                if key in ("qq_ws_url", "qq_token"):
                    flat[key] = value
                else:
                    flat[f"{section}_{key}"] = value
        flat["debug"] = data.get("debug", False)
        return cls(**flat)

