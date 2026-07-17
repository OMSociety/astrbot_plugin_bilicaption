import os
import re
import tempfile

import aiohttp
from bilibili_api import Credential, video
from pydantic import Field
from pydantic.dataclasses import dataclass

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import MessageChain
from astrbot.api.star import Context, Star, register
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool
from astrbot.core.astr_agent_context import AstrAgentContext
from astrbot.core.message.components import File as FileComponent
from astrbot.core.message.components import Plain

# BVID 格式预编译正则：BV开头，后续为字母或数字
BVID_PATTERN = re.compile(r"BV[a-zA-Z0-9]{10,12}")


class SubtitleFetchError(Exception):
    """字幕获取失败，异常消息可直接作为工具结果返回给用户"""


async def resolve_b23(short_url: str) -> str:
    """
    解析 b23.tv 短链，返回真实的长链接
    """
    timeout = aiohttp.ClientTimeout(total=10)

    if not short_url.startswith("http"):
        short_url = "https://" + short_url

    async with aiohttp.ClientSession(timeout=timeout) as session:
        # 第一次请求
        async with session.get(short_url, allow_redirects=False) as response:
            real_url = response.headers.get("Location", short_url)

        # 处理重定向
        max_redirects = 10
        for _ in range(max_redirects):
            if not real_url.startswith("http"):
                break
            async with session.get(real_url, allow_redirects=False) as response:
                next_url = response.headers.get("Location")
                if not next_url:
                    break
                real_url = next_url

    # 提取BVID
    match = BVID_PATTERN.search(real_url)

    logger.info(f"解析b23.tv短链成功：{short_url} -> {real_url}")

    bvid = match.group(0) if match else ""
    if not bvid:
        logger.error(f"解析b23.tv短链失败：{short_url} -> {real_url}")
        return "error"

    logger.info(f"解析视频链接成功：{short_url} -> {bvid}")

    return bvid


async def normalize_bvid(raw: str) -> str:
    """规范化输入为 BVID，支持 BV 号与 b23 短链。失败返回 'error'。"""
    if "b23" in raw:
        return await resolve_b23(raw)
    if BVID_PATTERN.match(raw):
        return raw
    # 兜底：按短链再试一次（兼容直接粘贴短码等情况）
    return await resolve_b23("https://b23.tv/" + raw)


async def fetch_subtitle(bvid: str, sessdata: str, bili_jct: str) -> tuple[str, str]:
    """
    获取视频标题与字幕全文，供各工具复用。
    成功返回 (title, subtitle_text)；失败抛 SubtitleFetchError。
    """
    credential = Credential(sessdata=sessdata, bili_jct=bili_jct)
    v = video.Video(bvid, credential=credential)

    try:
        # 1. 获取视频基础信息（可能抛网络异常或视频不存在的 API 异常）
        info = await v.get_info()
        title = info.get("title", "未知标题")

        # 2. 获取 CID
        cid = await v.get_cid(0)

        # 3. 获取字幕元数据
        subtitle_info = await v.get_subtitle(cid)
    except aiohttp.ClientError as e:
        logger.error(f"网络请求异常: {e}")
        raise SubtitleFetchError("网络请求异常，请稍后重试。") from e
    except Exception as e:
        logger.exception(f"获取视频信息失败: {bvid}")
        raise SubtitleFetchError(f"处理视频时发生内部错误: {e}") from e

    # 业务逻辑检查：是否有字幕数据
    if not subtitle_info or not subtitle_info.get("subtitles"):
        raise SubtitleFetchError(f"视频《{title}》暂无可用字幕。")

    # 优先寻找中文字幕 (zh-CN, zh-Hans)
    target_subtitle = None
    for sub in subtitle_info["subtitles"]:
        if sub.get("lan", "").startswith("zh"):
            target_subtitle = sub
            break

    # 兜底：取第一个
    if not target_subtitle:
        target_subtitle = subtitle_info["subtitles"][0]

    subtitle_url = target_subtitle.get("subtitle_url", "")
    if not subtitle_url:
        raise SubtitleFetchError("错误：字幕元数据中缺失 URL。")

    # 4. 下载字幕内容
    if not subtitle_url.startswith("http"):
        subtitle_url = "https:" + subtitle_url

    # 日志脱敏：去除 URL 参数，防止泄露签名
    log_url = subtitle_url.split("?")[0]
    logger.info(f"正在获取视频《{title}》字幕: {log_url}")

    timeout = aiohttp.ClientTimeout(total=15)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(subtitle_url) as resp:
                if resp.status != 200:
                    raise SubtitleFetchError(
                        f"下载字幕文件失败，HTTP 状态码: {resp.status}"
                    )
                subtitle_json = await resp.json()
    except aiohttp.ClientError as e:
        logger.error(f"网络请求异常: {e}")
        raise SubtitleFetchError("网络请求异常，请稍后重试。") from e

    # 5. 解析字幕正文
    body = subtitle_json.get("body", [])
    raw_text = "\n".join([item.get("content", "") for item in body])

    if not raw_text:
        raise SubtitleFetchError(f"视频《{title}》字幕内容解析为空。")

    return title, raw_text


def _truncate(text: str, max_len: int) -> str:
    """按上限截断字幕；max_len <= 0 表示不限制。"""
    if max_len > 0 and len(text) > max_len:
        logger.info(f"字幕过长 ({len(text)}字符)，已执行截断。")
        return text[:max_len] + "\n...(后续内容已省略)"
    return text


def _sanitize_filename(name: str, max_len: int = 50) -> str:
    """清理文件名，去除非法字符并截断。"""
    # 替换 Windows/Linux 文件名非法字符
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    if len(name) > max_len:
        name = name[:max_len].rstrip() + "..."
    return name or "unknown"


@dataclass(config={"arbitrary_types_allowed": True})
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

            # 写入文件
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"标题: {title}\nBVID: {bvid}\n{'=' * 40}\n\n{content}")

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
        except Exception as e:
            logger.error(f"发送字幕文件失败: {e}")

    async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs) -> str:
        # 1. 防御性检查
        config_err = self._check_config()
        if config_err:
            return config_err

        # 2. 格式校验与规范化
        bvid = await normalize_bvid(kwargs.get("bvid", "").strip())
        if bvid == "error":
            return "解析b23.tv短链失败，请检查链接是否正确"

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


@dataclass(config={"arbitrary_types_allowed": True})
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
        bvid = await normalize_bvid(kwargs.get("bvid", "").strip())
        if bvid == "error":
            return "解析b23.tv短链失败，请检查链接是否正确"

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


@register(
    "astrbot_plugin_bilicaption",
    "SodaCode & OMSociety",
    "获取B站视频字幕纯文本，不做AI总结，直接返回原始字幕。",
    "1.1.0",
)
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

        # 明确语义：不再使用有歧义的 'id'，统一读取 'bili_jct'
        # 如果用户配置了 'id'，代码逻辑上也可以尝试兼容读取，但优先使用正确键名
        sessdata = bilibili_cookie.get("sessdata", "")
        bili_jct = bilibili_cookie.get("bili_jct", bilibili_cookie.get("id", ""))
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
