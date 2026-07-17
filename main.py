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

        bvid = kwargs.get("bvid", "").strip()

        # 2. 格式校验
        if "b23" in bvid:
            bvid = await resolve_b23(bvid)
        elif not BVID_PATTERN.match(bvid):
            bvid = await resolve_b23("https://b23.tv/" + bvid)

        if bvid == "error":
            return "解析b23.tv短链失败，请检查链接是否正确"

        logger.info(f"开始解析视频：{bvid}")

        # 3. 初始化凭证
        credential = Credential(sessdata=self.sessdata, bili_jct=self.bili_jct)
        v = video.Video(bvid, credential=credential)

        try:
            # 4. 获取视频基础信息
            # 这一步可能抛出网络异常或视频不存在的 API 异常
            info = await v.get_info()
            title = info.get("title", "未知标题")

            # 5. 获取 CID
            cid = await v.get_cid(0)

            # 6. 获取字幕元数据
            subtitle_info = await v.get_subtitle(cid)

            # 业务逻辑检查：是否有字幕数据
            if not subtitle_info or not subtitle_info.get("subtitles"):
                return f"视频《{title}》暂无可用字幕。"

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
                return "错误：字幕元数据中缺失 URL。"

            # 7. 下载字幕内容
            if not subtitle_url.startswith("http"):
                subtitle_url = "https:" + subtitle_url

            # 日志脱敏：去除 URL 参数，防止泄露签名
            log_url = subtitle_url.split("?")[0]
            logger.info(f"正在获取视频《{title}》字幕: {log_url}")

            subtitle_text = ""
            timeout = aiohttp.ClientTimeout(total=15)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(subtitle_url) as resp:
                    if resp.status != 200:
                        return f"下载字幕文件失败，HTTP 状态码: {resp.status}"

                    # 使用 aiohttp 直接解析 json，避免手动 import json
                    subtitle_json = await resp.json()

            # 8. 解析与截断
            body = subtitle_json.get("body", [])
            raw_text = "\n".join([item.get("content", "") for item in body])

            # 长度控制：防止 LLM 上下文溢出
            if len(raw_text) > self.max_subtitle_length:
                logger.info(f"字幕过长 ({len(raw_text)}字符)，已执行截断。")
                raw_text = (
                    raw_text[: self.max_subtitle_length] + "\n...(后续内容已省略)"
                )

            subtitle_text = raw_text

            if not subtitle_text:
                return f"视频《{title}》字幕内容解析为空。"

            # 9. 自动发送 txt 文件（如果开启）
            if self.auto_send_txt:
                # 异步发送，不阻塞主流程
                await self._send_txt_file(context, title, bvid, subtitle_text)

            # 返回字幕纯文本，前附标题行
            return f"[字幕] {title}\n\n{subtitle_text}"

        except aiohttp.ClientError as e:
            logger.error(f"网络请求异常: {e}")
            return "网络请求异常，请稍后重试。"
        except KeyError as e:
            logger.error(f"数据解析异常，结构可能发生变更: {e}")
            return "解析字幕数据时发生错误，可能是 API 结构变更。"
        except Exception as e:
            # 捕获 bilibili_api 抛出的其他异常或未知异常
            # 建议在日志中打印完整堆栈
            logger.exception(f"处理 BVID {bvid} 时发生未知错误")
            return f"处理视频时发生内部错误: {str(e)}"


@register(
    "astrbot_plugin_bilicaption",
    "SodaCode & OMSociety",
    "获取B站视频字幕纯文本，不做AI总结，直接返回原始字幕。",
    "1.0.0",
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

        # 3. 配置完整性校验日志
        if not sessdata:
            logger.warning(
                "BiliCaption: SESSDATA 未配置，可能导致无法获取高质量字幕或鉴权失败。"
            )
        if not bili_jct:
            logger.warning("BiliCaption: bili_jct 未配置。")

        # 4. 注册工具
        tool = BilibiliTool(
            sessdata=sessdata,
            bili_jct=bili_jct,
            ct=self.context,
            max_subtitle_length=max_len,
            auto_send_txt=auto_send_txt,
        )
        self.context.add_llm_tools(tool)

    async def initialize(self):
        pass

    # @filter.command("bilicaption")
    # async def bilicaption(self, event: AstrMessageEvent):
    #     yield event.plain_result(
    #         "BiliCaption 插件已就绪。请直接发送 BVID 或让 AI 调用工具。"
    #     )

    async def terminate(self):
        pass
