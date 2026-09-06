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
from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from .subtitle_utils import (
    SubtitleFetchError,
    _sanitize_filename,
    _truncate,
    fetch_subtitle,
    normalize_bvid,
)


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class _BiliToolBase(FunctionTool[AstrAgentContext]):
    """bilibili 字幕类工具的公共基类：链接解析 → 字幕获取 → 截断/发文件。"""

    name: str = ""
    description: str = ""
    parameters: dict = Field(default_factory=dict)

    # 配置参数
    sessdata: str = ""
    bili_jct: str = ""
    # 字幕最大长度限制（0 表示不截断）
    max_subtitle_length: int = 0
    # 是否自动发送 txt 文件到聊天
    auto_send_txt: bool = False
    # 返回文本前缀，子类覆写
    result_prefix: str = "[字幕]"

    async def _send_txt_file(
        self,
        context: ContextWrapper[AstrAgentContext],
        title: str,
        bvid: str,
        content: str,
    ) -> None:
        """将字幕内容保存为 txt 文件并发送到当前会话。"""
        try:
            # 创建临时文件
            safe_title = _sanitize_filename(title)
            tmp_dir = tempfile.gettempdir()
            filepath = os.path.join(tmp_dir, f"{safe_title}_{bvid}.txt")

            # 写入文件（异步写，避免阻塞事件循环）
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(f"标题: {title}\nBVID: {bvid}\n{'=' * 40}\n\n{content}")

            logger.info(f"字幕已保存至: {filepath}")

            # 发送文件到当前会话
            agent_ctx = context.context
            session = agent_ctx.event.unified_msg_origin
            await agent_ctx.context.send_message(
                session,
                MessageChain(
                    [
                        FileComponent(
                            name=f"{safe_title}.txt",
                            file=filepath,
                        ),
                        Plain(text=f"已发送视频《{title}》的字幕文件"),
                    ]
                ),
            )
        except Exception as e:  # noqa: BLE001 - 兜底保护：发送失败只记日志，不影响主流程
            logger.error(f"发送字幕文件失败: {e}")
        finally:
            # 平台适配器在 send_message 内同步读取文件后上传，返回即可安全删除，
            # 否则长期运行的实例会在系统临时目录无限堆积
            try:
                os.remove(filepath)
            except OSError:
                pass

    async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs) -> str:
        # 1. 格式校验与规范化
        bvid_raw = (kwargs.get("bvid") or "").strip()
        if not bvid_raw:
            return "请提供 B 站视频链接、BV 号或 b23.tv 短链。"
        bvid = await normalize_bvid(bvid_raw)
        if bvid == "error":
            return "解析视频链接失败，请检查链接是否正确（支持 B 站完整链接 / BV 号 / b23.tv 短链）。"

        logger.info(f"[{self.name}] 开始解析视频：{bvid}")

        # 2. 获取字幕
        try:
            title, subtitle_text = await fetch_subtitle(
                bvid, self.sessdata, self.bili_jct
            )
        except SubtitleFetchError as e:
            return str(e)

        # 3. 自动发送 txt 文件（如果开启）：发送完整字幕，
        #    max_subtitle_length 截断只用于控制返回给 LLM 的上下文长度
        if self.auto_send_txt:
            await self._send_txt_file(context, title, bvid, subtitle_text)

        # 4. 长度控制：防止 LLM 上下文溢出
        subtitle_text = _truncate(subtitle_text, self.max_subtitle_length)

        # 返回字幕纯文本，前附标题行
        return f"{self.result_prefix} {title}\n\n{subtitle_text}"


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class BilibiliTool(_BiliToolBase):
    name: str = "bilibili_caption"
    description: str = "获取哔哩哔哩视频的字幕纯文本。如果视频没有字幕则返回提示信息。"
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "bvid": {
                    "type": "string",
                    "description": "想要获取的哔哩哔哩视频的BVID或是b23.tv链接，例如BV1GJ411x7h7或https://b23.tv/4bdIZBf",
                },
            },
            "required": ["bvid"],
        }
    )
    result_prefix: str = "[字幕]"


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class BilibiliReadTool(_BiliToolBase):
    name: str = "bilibili_read"
    description: str = (
        "通读哔哩哔哩视频的完整字幕以便你解读视频内容。"
        "当用户要求你解读、总结、分析、评价某个B站视频时调用，"
        "返回完整字幕原文供你通读，之后由你自行组织语言输出解读。"
        "注意：完整字幕会占用大量上下文，token 消耗较高，"
        "仅在用户明确要求深度解读视频内容时调用，普通字幕提取请使用 bilibili_caption。"
    )
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "bvid": {
                    "type": "string",
                    "description": "想要解读的哔哩哔哩视频的BVID或是b23.tv链接，例如BV1GJ411x7h7或https://b23.tv/4bdIZBf",
                },
            },
            "required": ["bvid"],
        }
    )
    result_prefix: str = "[完整字幕]"


class BiliCaption(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        # AstrBotConfig 是 dict 子类，直接按字典读取
        bilibili_cookie = config.get("bilibili_cookie", {})

        sessdata = bilibili_cookie.get("sessdata", "")
        bili_jct = bilibili_cookie.get("bili_jct", "")
        max_len = config.get("max_subtitle_length", 0)
        auto_send_txt = config.get("auto_send_txt", False)
        enable_read_tool = config.get("enable_read_tool", False)
        read_max_len = config.get("read_max_subtitle_length", 0)

        # 配置完整性校验日志
        if not sessdata:
            logger.warning(
                "BiliCaption: SESSDATA 未配置，可能导致无法获取高质量字幕或鉴权失败。"
            )
        if not bili_jct:
            logger.warning("BiliCaption: bili_jct 未配置。")

        # 注册字幕提取工具
        tool = BilibiliTool(
            sessdata=sessdata,
            bili_jct=bili_jct,
            max_subtitle_length=max_len,
            auto_send_txt=auto_send_txt,
        )
        self.context.add_llm_tools(tool)

        # 按需注册深度解读工具（高 token 消耗，默认关闭）
        if enable_read_tool:
            read_tool = BilibiliReadTool(
                sessdata=sessdata,
                bili_jct=bili_jct,
                max_subtitle_length=read_max_len,
            )
            self.context.add_llm_tools(read_tool)
            logger.info(
                "BiliCaption: bilibili_read 工具已注册（完整字幕通读，token 消耗较高）"
            )
