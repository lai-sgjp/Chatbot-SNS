import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TTSManager:
    """文本转语音管理器。

    目前支持 Edge-TTS（免费，无需 API Key），未来可扩展 GPT-SoVITS。
    Edge-TTS 默认中文语音：zh-CN-XiaoxiaoNeural (女声)
                           zh-CN-YunxiNeural (男声)
    """

    def __init__(
        self,
        voice: str = "zh-CN-XiaoxiaoNeural",
        rate: str = "+0%",
        volume: str = "+0%",
    ):
        self.voice = voice
        self.rate = rate
        self.volume = volume

    async def text_to_speech(self, text: str, output_path: Optional[str] = None) -> bytes:
        """将文本转为语音。

        Args:
            text: 要朗读的文本
            output_path: 可选，保存到文件

        Returns:
            音频字节数据 (mp3 格式)
        """
        try:
            import edge_tts
        except ImportError:
            logger.error("edge-tts 未安装，语音功能不可用")
            return b""

        communicate = edge_tts.Communicate(
            text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume,
        )

        if output_path:
            await communicate.save(output_path)
            with open(output_path, "rb") as f:
                return f.read()

        audio_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])
        return audio_buffer.getvalue()

    async def save_to_file(self, text: str, output_path: str) -> str:
        """将文本转为语音并保存到文件。"""
        await self.text_to_speech(text, output_path=output_path)
        return output_path

    def get_available_voices(self) -> list[dict]:
        """获取可用的语音列表。"""
        try:
            import edge_tts
            import asyncio
            voices = asyncio.run(edge_tts.list_voices())
            return [
                {"name": v["ShortName"], "locale": v["Locale"], "gender": v["Gender"]}
                for v in voices
            ]
        except ImportError:
            return []
