<p align="center"><strong>English</strong> · <a href="README.md">中文</a> · <a href="README_ru.md">Русский</a> · <a href="README_ja.md">日本語</a></p>

<div align="center">

<img src="https://raw.githubusercontent.com/OMSociety/astrbot_plugin_bilicaption/main/logo.png" width="120" alt="BiliCaption Logo" />

# 🎬 BiliCaption bilibili Subtitle Extraction & Reading

**bilibili video subtitle extraction and in-depth reading assistant** —— Plain-text subtitle extraction · Full transcript reading · Automatic link detection · Controllable length · txt file delivery

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/OMSociety/astrbot_plugin_bilicaption)
[![AstrBot](https://img.shields.io/badge/AstrBot-%E2%89%A5v4-green.svg)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/license-AGPL--3.0-orange.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/OMSociety/astrbot_plugin_bilicaption)](https://github.com/OMSociety/astrbot_plugin_bilicaption/stargazers)
[![Issues](https://img.shields.io/github/issues/OMSociety/astrbot_plugin_bilicaption)](https://github.com/OMSociety/astrbot_plugin_bilicaption/issues)

</div>

> 🎨 This project was written by AI · Source code is a fork of [SodaCodeSave/astrbot_plugin_biliread](https://github.com/SodaCodeSave/astrbot_plugin_biliread)

---

## ✨ Core Features

| Feature | Description |
|------|------|
| 📝 **Plain-text subtitle extraction** | Extracts the original subtitles of bilibili videos without AI summarization and returns them directly to the user |
| 🧠 **In-depth subtitle reading** | Feeds the full subtitles to the bot itself so it can interpret / summarize the video content (optional, high token usage) |
| 🔗 **Smart link detection** | Supports full bilibili links / BV IDs / b23.tv short links / bare short codes with automatic parsing |
| ✂️ **Length control** | The maximum returned subtitle length can be configured separately for each tool to prevent context overflow |
| 📄 **txt file delivery** | Optionally saves the full subtitles as a txt file and sends it to the chat |
| 🔒 **Login state support** | Full AI subtitles can be fetched after configuring bilibili Cookies (the subtitle API requires a logged-in state) |

---

## 📖 Feature Overview

### Subtitle extraction bilibili_caption
Send a bilibili link / BV ID directly in the chat, and the bot automatically calls the tool to return the plain-text subtitles.

### In-depth reading bilibili_read
When enabled, whenever you ask the bot to interpret a video it first reads through the full subtitles and then composes its answer.

### Difference between the two tools

| Feature | `bilibili_caption` | `bilibili_read` |
|:----|:-------------------|:----------------|
| Positioning | Quickly extracts the original subtitle text | In-depth interpretation for the bot's own reading |
| Returns | Subtitle text for the AI to show the user | Full subtitles fed into the bot's reasoning |
| Token usage | Controllable (can be truncated) | Relatively high (reads the full text by default) |
| Enabled by default | ✅ Always available | ❌ Off by default; must be enabled in the configuration |

---

## 🚀 Quick Start

### Step 1: Installation

**Method 1: Plugin marketplace**
- AstrBot WebUI → Plugin Marketplace → search for `bilicaption`

**Method 2: GitHub repository**
- AstrBot WebUI → Plugin Management → ＋ Install
- Paste the repository URL: `https://github.com/OMSociety/astrbot_plugin_bilicaption`

> 💡 Dependencies (bilibili-api-python / aiohttp / aiofiles) are installed automatically from `requirements.txt` when the plugin is installed; no manual installation is required.

### Step 2: Configure bilibili Cookies (required)

> 💡 The bilibili subtitle API requires a logged-in state, and **subtitles cannot be fetched without configuring Cookies** (AI subtitles are hidden from anonymous users). Configure them before use.

Fill in the `bilibili_cookie` group of the plugin configuration:

| Field | How to obtain |
|:----|:----|
| `sessdata` | Log in to [bilibili.com](https://www.bilibili.com) in your browser → F12 → Application → Cookies → copy the value of `SESSDATA` |
| `bili_jct` | Same as above; copy the value of `bili_jct` |

### Step 3: Restart to apply

After configuring, reload the plugin in the WebUI (or restart AstrBot), then send a bilibili link in the chat to test.

---

## ⚙️ Configuration Options

| Option | Type | Default | Description |
|:------|:-----|:-------|:-----|
| `bilibili_cookie.sessdata` | string | `""` | bilibili SESSDATA Cookie (required; the subtitle API requires a logged-in state) |
| `bilibili_cookie.bili_jct` | string | `""` | bilibili bili_jct Cookie |
| `max_subtitle_length` | int | `0` | Maximum number of subtitle characters returned by the caption tool; `0` means no limit |
| `auto_send_txt` | bool | `false` | When enabled, extracted subtitles are automatically sent to the chat as a txt file |
| `enable_read_tool` | bool | `false` | Enables the `bilibili_read` in-depth reading tool (high token usage) |
| `read_max_subtitle_length` | int | `0` | Maximum number of subtitle characters returned by the read tool; `0` means no limit (full-text reading) |

### Quick configuration template

Fill in the settings via the WebUI configuration panel, or refer to the following structure (`data/config/astrbot_plugin_bilicaption_config.json`):

```json
{
  "bilibili_cookie": {
    "sessdata": "YOUR_SESSDATA",
    "bili_jct": "YOUR_BILI_JCT"
  },
  "max_subtitle_length": 0,
  "auto_send_txt": false,
  "enable_read_tool": false,
  "read_max_subtitle_length": 0
}
```

---

## 🛠️ LLM-Callable Tools

The plugin registers 2 LLM tools (`bilibili_read` requires enabling the `enable_read_tool` option). The model decides on its own when to call them; just state your request in natural language:

```
User: Extract the subtitles for this video https://b23.tv/4bdIZBf
🤖 → bilibili_caption(bvid=https://b23.tv/4bdIZBf)
    [Subtitles] "A Brief History of AI: From Turing to GPT"
    Hello everyone, and welcome to this video...

User: Walk me through this video BV1GJ411x7h7
🤖 → bilibili_read(bvid=BV1GJ411x7h7)
    (Reads through the full subtitles, then composes its own interpretation)
```

### bilibili_caption
Returns the plain-text subtitles of a bilibili video. If the video has no subtitles, a notice is returned instead.

| Parameter | Type | Required | Description |
|:----|:----|:----:|:-----|
| `bvid` | string | ✅ | BVID / full bilibili link / b23.tv short link, e.g. `BV1GJ411x7h7` or `https://b23.tv/4bdIZBf` |
| `page` | integer | ❌ | Part number, starting from 1, default 1. Not needed for single-part videos |

### bilibili_read (requires enabling the `enable_read_tool` option)
Reads through the full subtitles of a bilibili video so the bot can interpret its content. Called when the user asks to summarize, analyze, or evaluate a bilibili video.

| Parameter | Type | Required | Description |
|:----|:----|:----:|:-----|
| `bvid` | string | ✅ | BVID / full bilibili link / b23.tv short link |
| `page` | integer | ❌ | Part number, starting from 1, default 1. Not needed for single-part videos |

> Note: `bilibili_read` returns the full original subtitles without adding any preset prompts. The bot reads them itself and decides how to interpret the video.

---

## ⚠️ FAQ

### Q1: Does it require configuration?

**Yes**. The bilibili subtitle API requires a logged-in state; configure `bilibili_cookie.sessdata` and `bili_jct` (see [Quick Start](#-quick-start)).

### Q2: Can subtitles be fetched for every video?

No. For videos where the uploader has not uploaded subtitles and bilibili provides no AI subtitles, the content cannot be fetched; the plugin will report "No subtitles available".

### Q3: Why no AI summarization?

`bilibili_caption` is designed for verbatim extraction. `bilibili_read` instead leaves summarization to the bot itself, without preset prompts.

### Q4: What is the difference between `bilibili_caption` and `bilibili_read`?

caption quickly returns the subtitle text for you to read; read feeds the full text to the bot, which reads it through before producing its interpretation. read costs more tokens but yields higher-quality interpretation. The two do not replace each other; toggle them as needed.

### Q5: How does it differ from BiliRead?

BiliRead calls a third-party LLM to summarize subtitles; this plugin skips the third-party LLM and either returns the original subtitles directly or uses the current bot itself for interpretation.

## 📝 Changelog

> 📋 **[View changelog →](CHANGELOG.md)**

---

## ⭐ Support This Project

If this plugin helps you, please consider giving it a Star ⭐. For issues and suggestions, open an [Issue](https://github.com/OMSociety/astrbot_plugin_bilicaption/issues) or a [Pull Request](https://github.com/OMSociety/astrbot_plugin_bilicaption/pulls).

## 🙏 Acknowledgements

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) open-source chatbot framework
- [SodaCodeSave/astrbot_plugin_biliread](https://github.com/SodaCodeSave/astrbot_plugin_biliread) upstream plugin (AGPL-3.0)

---

## 📜 License

This project is licensed under **AGPL-3.0** (inherited from the upstream BiliRead).

---

## 👤 Author

[@OMSociety](https://github.com/OMSociety)
