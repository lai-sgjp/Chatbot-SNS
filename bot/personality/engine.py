from dataclasses import dataclass, field
from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)


@dataclass
class CharacterCard:
    name: str = "助手"
    description: str = "一个友好的智能助手"
    personality: str = "友善、耐心、乐于助人"
    speaking_style: str = "用中文自然交流，语气温和"
    rules: list[str] = field(default_factory=lambda: [
        "不要透露你是AI助手",
        "回答要简洁清晰",
    ])
    voice_params: dict = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "CharacterCard":
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        names = set(cls.__dataclass_fields__)
        kwargs = {k: v for k, v in data.items() if k in names}
        return cls(**kwargs)


class PersonalityEngine:
    def __init__(self, card_dir: str | Path, card_name: str = "default"):
        self._card_dir = Path(card_dir)
        self._card_name = card_name
        self._card = self._load_card()

    def _load_card(self) -> CharacterCard:
        path = self._card_dir / f"{self._card_name}.yml"
        if path.exists():
            card = CharacterCard.from_yaml(path)
            logger.info("Loaded character card: %s", card.name)
            return card
        logger.warning("Character card not found at %s, using defaults", path)
        return CharacterCard()

    def build_system_prompt(self) -> str:
        c = self._card
        parts = [
            f"你是{c.name}。",
            f"性格：{c.personality}",
            f"说话风格：{c.speaking_style}",
            f"{c.description}",
            "规则：",
        ]
        for rule in c.rules:
            parts.append(f"- {rule}")
        return "\n".join(parts)
