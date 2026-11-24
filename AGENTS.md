# AGENTS.md

AstrBot 插件：读取 B 站视频字幕，向 LLM 暴露工具 `bili_view` 与 `bili_caption`。MaiBot 姊妹仓库 `maibot_plugin_bilicaption` 与本仓库共用同一套字幕逻辑。

## 验收命令

```
pip install -r requirements.txt pytest pytest-asyncio ruff
ruff format .
ruff check .
pytest
```

- 三项全绿才算通过；`bilibili-api-python` 必须是 17.x（`requirements.txt` 约束）。
- 系统临时目录不可写时给 `pytest` 加 `--basetemp=<可写目录>`。

## 目录职责

- `main.py`：两个工具与 Star 入口；只做框架适配。
- `subtitle_utils.py`：链接解析、字幕获取、缓存、长度保护。
- `tests/`：以桩替代网络，不得发起真实请求；`tests/conftest.py` 在未安装 AstrBot 时提供 `astrbot.api.logger` 替身。

## 规则

- 改 `subtitle_utils.py` → 同步更新 MaiBot 仓库的同名文件（该仓库版本不含 `_sanitize_filename`）并分别跑两边测试；原因：两端各存一份，函数签名与行为必须一致。
- 改配置字段 → 同步改 `_conf_schema.json` 与 `.astrbot-plugin/i18n/` 四语文件、README 四语配置表。
- 对用户可见的字幕失败原因必须是 `SubtitleFetchError` / `BvidParseError` 的消息；原因：工具直接把 `str(e)` 返回给 LLM，不得吞异常或返回笼统文案。
- 每一跳短链重定向都必须过 `_is_safe_b23_url`；原因：重定向目标可被诱导到内网（SSRF）。
- `metadata.yaml` 的 `version` 与 `CHANGELOG.md` 最新条目、README 徽章同步修改。
- `README*.md` 与 `CHANGELOG.md` 不使用 emoji；`CHANGELOG.md` 中文在上英文在下，条目一一对应。
