import pytest
import yaml
from bot.personality.engine import PersonalityEngine, CharacterCard


def test_default_card(tmp_path):
    card_dir = tmp_path / "cards"
    card_dir.mkdir()
    card_data = {
        "name": "测试角色",
        "personality": "测试性格",
        "speaking_style": "测试风格",
    }
    with open(card_dir / "test.yml", "w", encoding="utf-8") as f:
        yaml.dump(card_data, f)
    engine = PersonalityEngine(card_dir=card_dir, card_name="test")
    prompt = engine.build_system_prompt()
    assert "测试角色" in prompt
    assert "测试性格" in prompt
    assert "测试风格" in prompt


def test_missing_card(tmp_path):
    card_dir = tmp_path / "nonexistent"
    engine = PersonalityEngine(card_dir=card_dir, card_name="missing")
    prompt = engine.build_system_prompt()
    assert "助手" in prompt


def test_card_from_yaml(tmp_path):
    card_data = {
        "name": "自定义角色",
        "rules": ["规则1", "规则2"],
    }
    path = tmp_path / "card.yml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(card_data, f)
    card = CharacterCard.from_yaml(path)
    assert card.name == "自定义角色"
    assert card.rules == ["规则1", "规则2"]
