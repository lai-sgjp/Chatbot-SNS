import pytest
import yaml
from bot.config import BotConfig


def test_default_config():
    config = BotConfig()
    assert config.llm.provider == "openai"
    assert config.debug is False


def test_from_yaml(tmp_path):
    cfg_file = tmp_path / "config.yml"
    data = {"llm": {"model": "gpt-3.5-turbo"}, "debug": True}
    with open(cfg_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f)
    config = BotConfig.from_yaml(cfg_file)
    assert config.llm.model == "gpt-3.5-turbo"
    assert config.debug is True


def test_yaml_not_found():
    config = BotConfig.from_yaml("nonexistent.yml")
    assert config.llm.provider == "openai"


def test_env_override(monkeypatch):
    monkeypatch.setenv("BOT_LLM_MODEL", "gpt-4-turbo")
    config = BotConfig()
    assert config.llm.model == "gpt-4-turbo"
