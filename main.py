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
class BilibiliTool(FunctionTool[AstrAgentContext]):
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

    # 配置参数
    sessdata: str = ""
    bili_jct: str = ""
    ct: Context = Field(default=None)
    # 字幕最大长度限制（0 表示不截断）
    max_subtitle_length: int = 0
    # 是否自动发送 txt 文件到聊天
    auto_send_txt: bool = False

    def _check_config(self) -> str | None:
        """防御性检查：确保核心依赖已注入"""
        if not self.ct:
            return "插件内部错误：上下文未注入"
        return None

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

    async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs) -> str:
        # 1. 防御性检查
        config_err = self._check_config()
        if config_err:
            return config_err

        # 2. 格式校验与规范化
        bvid_raw = (kwargs.get("bvid") or "").strip()
        if not bvid_raw:
            return "请提供要获取字幕的 B 站视频链接、BV 号或 b23.tv 短链。"
        bvid = await normalize_bvid(bvid_raw)
        if bvid == "error":
            return "解析视频链接失败，请检查链接是否正确（支持 B 站完整链接 / BV 号 / b23.tv 短链）。"

        logger.info(f"开始解析视频：{bvid}")

        # 3. 获取字幕
        try:
            title, subtitle_text = await fetch_subtitle(
                bvid, self.sessdata, self.bili_jct
            )
        except SubtitleFetchError as e:
            return str(e)

        # 4. 长度控制：防止 LLM 上下文溢出
        subtitle_text = _truncate(subtitle_text, self.max_subtitle_length)

        # 5. 自动发送 txt 文件（如果开启）
        if self.auto_send_txt:
            await self._send_txt_file(context, title, bvid, subtitle_text)

        # 返回字幕纯文本，前附标题行
        return f"[字幕] {title}\n\n{subtitle_text}"


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class BilibiliReadTool(FunctionTool[AstrAgentContext]):
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

    # 配置参数
    sessdata: str = ""
    bili_jct: str = ""
    ct: Context = Field(default=None)
    # 字幕最大长度限制（0 表示不截断，即全文通读）
    max_subtitle_length: int = 0

    def _check_config(self) -> str | None:
        """防御性检查：确保核心依赖已注入"""
        if not self.ct:
            return "插件内部错误：上下文未注入"
        return None

    async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs) -> str:
        # 1. 防御性检查
        config_err = self._check_config()
        if config_err:
            return config_err

        # 2. 格式校验与规范化
        bvid_raw = (kwargs.get("bvid") or "").strip()
        if not bvid_raw:
            return "请提供要解读的 B 站视频链接、BV 号或 b23.tv 短链。"
        bvid = await normalize_bvid(bvid_raw)
        if bvid == "error":
            return "解析视频链接失败，请检查链接是否正确（支持 B 站完整链接 / BV 号 / b23.tv 短链）。"

        logger.info(f"[bilibili_read] 开始通读视频：{bvid}")

        # 3. 获取字幕
        try:
            title, subtitle_text = await fetch_subtitle(
                bvid, self.sessdata, self.bili_jct
            )
        except SubtitleFetchError as e:
            return str(e)

        # 4. 长度控制（默认不截断，全文通读）
        subtitle_text = _truncate(subtitle_text, self.max_subtitle_length)

        # 返回完整字幕原文，由 bot 自行阅读并输出解读
        return f"[完整字幕] {title}\n\n{subtitle_text}"


class BiliCaption(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)

        # 1. 安全的配置读取
        # 兼容 config 是字典或 Pydantic 对象的情况
        if isinstance(config, dict):
            plugin_config = config
        elif hasattr(config, "model_dump"):
            # Pydantic v2
            plugin_config = config.model_dump()
        elif hasattr(config, "dict"):
            # Pydantic v1
            plugin_config = config.dict()
        else:
            logger.warning(f"不支持的配置类型: {type(config)}，使用默认空配置。")
            plugin_config = {}

        # 2. 提取配置项
        bilibili_cookie = plugin_config.get("bilibili_cookie", {})

        sessdata = bilibili_cookie.get("sessdata", "")
        bili_jct = bilibili_cookie.get("bili_jct", "")
        max_len = plugin_config.get("max_subtitle_length", 0)
        auto_send_txt = plugin_config.get("auto_send_txt", False)
        enable_read_tool = plugin_config.get("enable_read_tool", False)
        read_max_len = plugin_config.get("read_max_subtitle_length", 0)

        # 3. 配置完整性校验日志
        if not sessdata:
            logger.warning(
                "BiliCaption: SESSDATA 未配置，可能导致无法获取高质量字幕或鉴权失败。"
            )
        if not bili_jct:
            logger.warning("BiliCaption: bili_jct 未配置。")

        # 4. 注册字幕提取工具
        tool = BilibiliTool(
            sessdata=sessdata,
            bili_jct=bili_jct,
            ct=self.context,
            max_subtitle_length=max_len,
            auto_send_txt=auto_send_txt,
        )
        self.context.add_llm_tools(tool)

        # 5. 按需注册深度解读工具（高 token 消耗，默认关闭）
        if enable_read_tool:
            read_tool = BilibiliReadTool(
                sessdata=sessdata,
                bili_jct=bili_jct,
                ct=self.context,
                max_subtitle_length=read_max_len,
            )
            self.context.add_llm_tools(read_tool)
            logger.info(
                "BiliCaption: bilibili_read 工具已注册（完整字幕通读，token 消耗较高）"
            )

    async def initialize(self):
        pass

    async def terminate(self):
        pass
