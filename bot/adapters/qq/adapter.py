import json
import asyncio
import logging
from typing import Optional

from bot.models import Message, Reply
from bot.adapters.base import BaseAdapter
from . import onebot

logger = logging.getLogger(__name__)


class QQAdapter(BaseAdapter):
    """QQ 适配器：通过 OneBot v11 WebSocket 协议收发消息。

    需要配合 OneBot 实现（如 Lagrange / go-cqhttp / NapCat）使用。
    连接方式：正向 WebSocket 客户端连接到 OneBot 的 WebSocket 服务器。
    """

    def __init__(
        self,
        pipeline,
        ws_url: str = "ws://localhost:8080",
        token: str = "",
    ):
        self._pipeline = pipeline
        self._ws_url = ws_url
        self._token = token
        self._running = False
        self._ws = None

    async def start(self):
        self._running = True
        logger.info("QQ适配器启动，连接至 %s", self._ws_url)
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        try:
            import aiohttp
            session = aiohttp.ClientSession(headers=headers)
            async with session.ws_connect(self._ws_url) as ws:
                self._ws = ws
                logger.info("QQ WebSocket 已连接")
                async for msg in ws:
                    if not self._running:
                        break
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self._handle_event(json.loads(msg.data))
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error("WebSocket 连接错误: %s", ws.exception())
                        break
        except aiohttp.ClientConnectorError as e:
            logger.error("无法连接到 OneBot 服务端 (%s): %s", self._ws_url, e)
        except asyncio.CancelledError:
            pass
        finally:
            self._running = False
            logger.info("QQ适配器已断开")

    async def _handle_event(self, event: dict):
        post_type = event.get("post_type")
        if post_type == onebot.POST_TYPE_META_EVENT:
            meta_type = event.get("meta_event_type")
            if meta_type == onebot.META_EVENT_LIFECYCLE:
                logger.info("OneBot 生命周期事件: %s", event.get("sub_type", "connect"))
            return

        if post_type != onebot.POST_TYPE_MESSAGE:
            return

        user_id = str(event.get("user_id", ""))
        group_id = event.get("group_id")
        message_text = event.get("raw_message", "")

        if not message_text:
            return

        session_id = f"group_{group_id}" if group_id else f"private_{user_id}"

        message = Message(
            text=message_text,
            user_id=user_id,
            user_name=f"QQ_{user_id}",
            session_id=session_id,
        )

        reply = await self._pipeline.process(message)
        if reply.text:
            await self._send_reply(event, reply.text)

    async def _send_reply(self, event: dict, text: str):
        if not self._ws:
            return
        if event.get("message_type") == onebot.MESSAGE_TYPE_PRIVATE:
            payload = onebot.build_send_private_msg(event["user_id"], text)
        else:
            payload = onebot.build_send_group_msg(event["group_id"], text)
        await self._ws.send_json(payload)

    async def send(self, reply: Reply):
        """Pipeline 调用此方法发送主动消息（当前暂未实现主动发送）。"""
        if reply.text:
            logger.info("QQ 主动消息 (未实现): %s", reply.text[:50])

    async def stop(self):
        self._running = False
        if self._ws and not self._ws.closed:
            await self._ws.close()
