import asyncio
import logging
from datetime import datetime

from bot.models import Message, Reply
from bot.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)


class TerminalAdapter(BaseAdapter):
    def __init__(self, pipeline, user_id: str = "terminal_user", user_name: str = "你"):
        self._pipeline = pipeline
        self._user_id = user_id
        self._user_name = user_name
        self._running = False

    async def start(self):
        self._running = True
        logger.info("终端适配器启动，输入消息开始对话（输入 /exit 退出）")
        print("\n=== 聊天机器人已启动 ===")
        print("输入消息开始对话，输入 /exit 退出\n")

        while self._running:
            try:
                text = await asyncio.get_event_loop().run_in_executor(
                    None, input, f"{self._user_name}: "
                )
                if not text:
                    continue
                if text.strip() == "/exit":
                    break

                message = Message(
                    text=text,
                    user_id=self._user_id,
                    user_name=self._user_name,
                    session_id="terminal",
                )

                reply = await self._pipeline.process(message)
                await self.send(reply)
            except EOFError:
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("处理消息时出错：%s", e)
                print(f"[Error] {e}")

    async def send(self, reply: Reply):
        if reply.text:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] 助手: {reply.text}\n")

    async def stop(self):
        self._running = False
