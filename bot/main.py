import asyncio
import signal
import sys
from pathlib import Path

from loguru import logger

from bot.config import BotConfig
from bot.event_bus import EventBus
from bot.llm.openai_engine import OpenAIEngine
from bot.personality.engine import PersonalityEngine
from bot.pipeline import MessagePipeline
from bot.adapters.terminal.adapter import TerminalAdapter


def setup_logging(debug: bool = False):
    level = "DEBUG" if debug else "INFO"
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | <cyan>{name}</cyan> | {message}",
    )
    logger.add(
        "data/logs/bot_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        rotation="1 day",
        retention="7 days",
    )


def _check_config(config: BotConfig):
    """启动时检查配置，给出有用的提示。"""
    key = config.llm_api_key
    if not key or key == "sk-placeholder":
        logger.warning(
            "LLM API Key 未配置！请编辑 config.yml 设置 llm.api_key，"
            "或设置环境变量 BOT_LLM_API_KEY"
        )
        return False

    base = config.llm_base_url
    if "api.openai.com" in base and not key.startswith("sk-"):
        logger.warning(
            "base_url 指向 OpenAI 官方，但 API Key 格式似乎不对 "
            "(应以 sk- 开头)"
        )
    elif "localhost" in base or "127.0.0.1" in base:
        logger.info("base_url 指向本地地址，确认 Ollama 或其他本地服务已启动")

    logger.info(
        "LLM 配置: {} @ {} 模型={} max_tokens={}",
        config.llm_provider, config.llm_base_url,
        config.llm_model, config.llm_max_tokens,
    )
    return True


async def main():
    # 优先加载 config.yml（用户私有），其次是 config.example.yml（示例）
    for candidate in ["config.yml", "config.example.yml"]:
        config_path = Path(candidate)
        if config_path.exists():
            break
    else:
        config_path = None

    config = BotConfig.from_yaml(config_path) if config_path else BotConfig()
    setup_logging(config.debug)

    logger.info("ChatBot SNS v0.1.0 启动中...")

    if config.debug:
        logger.debug("加载的配置: {}", config.model_dump())

    event_bus = EventBus()

    api_key = config.llm_api_key or "sk-placeholder"
    llm_engine = OpenAIEngine(
        api_key=api_key,
        base_url=config.llm_base_url,
        model=config.llm_model,
        temperature=config.llm_temperature,
        max_tokens=config.llm_max_tokens,
    )

    personality_engine = PersonalityEngine(
        card_dir=config.personality_card_dir,
        card_name=config.personality_default_card,
    )

    pipeline = MessagePipeline(
        llm_engine=llm_engine,
        personality_engine=personality_engine,
        event_bus=event_bus,
        short_term_size=config.memory_short_term_size,
    )

    if config.adapter_adapter == "terminal":
        adapter = TerminalAdapter(pipeline=pipeline)
    else:
        raise ValueError(f"不支持的适配器: {config.adapter_adapter}")

    if not _check_config(config):
        logger.warning("配置不完整，仍可启动但 LLM 调用会失败")

    stop_event = asyncio.Event()

    def _signal_handler():
        logger.info("收到中断信号，正在关闭...")
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            pass

    try:
        await adapter.start()
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("程序退出")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
