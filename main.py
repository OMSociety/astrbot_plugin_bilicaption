import os
import tempfile

import aiofiles
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import MessageChain
from astrbot.api.star import Context, Star
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool
from astrbot.core.astr_agent_context import AstrAgentContext
from astrbot.core.message.components import File as FileComponent
from astrbot.core.message.components import Plain
from bilibili_api import Credential
from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from .subtitle_utils import (
    SubtitleCache,
    SubtitleFetchError,
    _sanitize_filename,
    load_subtitle,
    render_view,
)

_VIDEO_PARAM = {
    "type": "string",
    "description": "B 站视频的 BV 号、av 号、完整链接、b23.tv 短链或包含它们的分享文本",
}
_PAGE_PARAM = {
    "type": "integer",
    "description": "分 P 号，从 1 开始计数；仅当用户明确提到分 P 时才传。",
}


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class _BiliToolBase(FunctionTool[AstrAgentContext]):
    """B 站字幕工具公共基类：登录凭据、缓存与参数归一。"""

    name: str = ""
    description: str = ""
    parameters: dict = Field(default_factory=dict)

    credential: Credential | None = None
    cache: SubtitleCache = Field(default_factory=lambda: SubtitleCache(0, 0))

    @staticmethod
    def _int_arg(kwargs: dict, key: str) -> int | None:
        raw = kwargs.get(key)
        if raw is None:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError) as e:
            raise SubtitleFetchError(f"{key} 必须是整数。") from e


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class BiliViewTool(_BiliToolBase):
    name: str = "bili_view"
    description: str = (
        "读取哔哩哔哩视频的字幕，用于理解、总结、评价或回答关于视频内容的问题。"
        "支持 BV 号、av 号、完整视频链接、b23.tv / bili2233.cn 短链以及分享文本。"
        "字幕过长时只返回开头与结尾，并在结果里给出 offset，用它继续读取中间部分。"
        "如果用户要的是字幕文本或字幕文件本身，请改用 bili_caption。"
    )
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "video": _VIDEO_PARAM,
                "page": _PAGE_PARAM,
                "offset": {
                    "type": "integer",
                    "description": "从该字符位置起继续读取；仅在上次结果提示可继续读取时传。",
                },
            },
            "required": ["video"],
        }
    )
    max_chars: int = 20000

    async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs) -> str:
        try:
            page = self._int_arg(kwargs, "page")
            offset = self._int_arg(kwargs, "offset")
            result = await load_subtitle(
                kwargs.get("video") or "", page, self.credential, self.cache
            )
            return render_view(result.title, result.text, self.max_chars, offset)
        except SubtitleFetchError as e:
            return str(e)


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class BiliCaptionTool(_BiliToolBase):
    name: str = "bili_caption"
    description: str = (
        "获取哔哩哔哩视频的字幕原文（不限长度）。"
        "当用户要字幕文本或字幕文件时使用；"
        "如果用户想让你理解、总结、评价或回答视频内容，请改用 bili_view。"
    )
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {"video": _VIDEO_PARAM, "page": _PAGE_PARAM},
            "required": ["video"],
        }
    )
    auto_send_txt: bool = False

    async def _send_txt_file(
        self,
        context: ContextWrapper[AstrAgentContext],
        title: str,
        content: str,
    ) -> None:
        """将字幕保存为 txt 文件并发送到当前会话。"""
        safe_title = _sanitize_filename(title)
        filepath = os.path.join(
            tempfile.gettempdir(), f"{safe_title}_{os.getpid()}.txt"
        )
        try:
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(f"标题: {title}\n{'=' * 40}\n\n{content}")
            agent_ctx = context.context
            await agent_ctx.context.send_message(
                agent_ctx.event.unified_msg_origin,
                MessageChain(
                    [
                        FileComponent(name=f"{safe_title}.txt", file=filepath),
                        Plain(text=f"已发送视频《{title}》的字幕文件"),
                    ]
                ),
            )
        except Exception as e:  # noqa: BLE001 - 发送失败只记日志，字幕仍返回给 LLM
            logger.error(f"发送字幕文件失败: {e}")
        finally:
            # 适配器在 send_message 内同步读取文件，返回后删除以免临时目录堆积
            try:
                os.remove(filepath)
            except OSError:
                pass

    async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs) -> str:
        try:
            page = self._int_arg(kwargs, "page")
            result = await load_subtitle(
                kwargs.get("video") or "", page, self.credential, self.cache
            )
        except SubtitleFetchError as e:
            return str(e)
        if self.auto_send_txt:
            await self._send_txt_file(context, result.title, result.text)
        return f"[字幕] {result.title}\n\n{result.text}"


class BiliCaption(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        cookie = config.get("bilibili_cookie", {})
        sessdata = cookie.get("sessdata", "")
        bili_jct = cookie.get("bili_jct", "")
        credential = (
            Credential(sessdata=sessdata, bili_jct=bili_jct) if sessdata else None
        )
        if credential is None:
            logger.warning("BiliCaption: SESSDATA 未配置，无法读取 B 站字幕。")

        # 两个工具共用同一份缓存
        cache = SubtitleCache(
            config.get("cache_ttl_seconds", 3600), config.get("cache_max_entries", 64)
        )
        self.context.add_llm_tools(
            BiliViewTool(
                credential=credential,
                cache=cache,
                max_chars=config.get("view_max_chars", 20000),
            ),
            BiliCaptionTool(
                credential=credential,
                cache=cache,
                auto_send_txt=config.get("auto_send_txt", False),
            ),
        )
