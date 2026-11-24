<p align="center"><strong>English</strong> · <a href="README.md">中文</a> · <a href="README_ru.md">Русский</a> · <a href="README_ja.md">日本語</a></p>

<div align="center">

<h1><img src="https://raw.githubusercontent.com/OMSociety/astrbot_plugin_bilicaption/main/logo.png" width="192" alt="BiliCaption Logo"><br>BiliCaption bilibili Subtitle Extraction & Reading</h1>

**bilibili video subtitle reading assistant** —— Understand and summarize videos · Raw subtitle text · Many link formats · Paging for long subtitles · Result cache

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/OMSociety/astrbot_plugin_bilicaption)
[![AstrBot](https://img.shields.io/badge/AstrBot-%E2%89%A5v4-green.svg)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/license-AGPL--3.0-orange.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/OMSociety/astrbot_plugin_bilicaption)](https://github.com/OMSociety/astrbot_plugin_bilicaption/stargazers)
[![Issues](https://img.shields.io/github/issues/OMSociety/astrbot_plugin_bilicaption)](https://github.com/OMSociety/astrbot_plugin_bilicaption/issues)

</div>

> This project was written by AI · Source code is a fork of [SodaCodeSave/astrbot_plugin_biliread](https://github.com/SodaCodeSave/astrbot_plugin_biliread)

---

## Features

| Feature | Description |
|---|---|
| **Understand a video: `bili_view`** | Reads subtitles so the bot can understand, summarize, or review a video; 20000 characters per call by default, keeps the head and tail when longer and pages through the rest with `offset` |
| **Raw subtitles: `bili_caption`** | Returns the complete subtitles with no length limit; can optionally save them as a txt file and send it to the chat |
| **Many link formats** | BV ID / av number / full link / b23.tv and bili2233.cn short links / whole share text; `?p=N` selects the part automatically |
| **Result cache** | Shared by both tools, 1 hour and 64 entries by default; paging does not repeat requests |
| **Clear failure reasons** | Video not found, no subtitles, login expired, risk control, and network timeout each return a specific message |

## Which tool

| The user wants | Tool |
|:----|:----|
| To understand, summarize, or review a video, or to ask about its content | `bili_view` |
| The subtitle text itself, or a subtitle txt file | `bili_caption` |

---

## Quick Start

1. Install: AstrBot WebUI → Plugin Market → search `bilicaption`. Dependencies (bilibili-api-python 17.x / aiohttp / aiofiles) are installed from `requirements.txt` automatically.
2. Fill in the cookie (required): the Bilibili subtitle API needs a login session. In the `bilibili_cookie` group, set `sessdata` (log in at [bilibili.com](https://www.bilibili.com) → F12 → Application → Cookies → copy the value of `SESSDATA`) and optionally `bili_jct`.
3. Reload the plugin in the WebUI and send a Bilibili link in chat.

## Configuration

| Option | Type | Default | Description |
|:------|:-----|:-------|:-----|
| `bilibili_cookie.sessdata` | string | `""` | Bilibili SESSDATA cookie (required) |
| `bilibili_cookie.bili_jct` | string | `""` | Bilibili bili_jct cookie |
| `view_max_chars` | int | `20000` | Maximum characters `bili_view` returns per call; `0` means no limit |
| `auto_send_txt` | bool | `false` | When enabled, `bili_caption` sends a subtitle txt file to the chat |
| `cache_ttl_seconds` | int | `3600` | Subtitle cache TTL in seconds; `0` disables the cache |
| `cache_max_entries` | int | `64` | Maximum cached entries; the least recently used entry is evicted when exceeded |

## Tools

### bili_view

| Parameter | Type | Required | Description |
|:----|:----|:----:|:-----|
| `video` | string | Yes | BV ID / av number / full link / short link / share text containing a link |
| `page` | integer | No | Part number starting at 1; may be omitted when the link has `?p=N` |
| `offset` | integer | No | Continue reading from this character position when the result says more is available |

When the subtitles exceed `view_max_chars`, the result keeps the first 60% and last 40% and reports the total length, the omitted ratio, and the usable `offset`.

### bili_caption

| Parameter | Type | Required | Description |
|:----|:----|:----:|:-----|
| `video` | string | Yes | Same as above |
| `page` | integer | No | Part number starting at 1 |

## FAQ

**Is configuration required?** Yes. The subtitle API needs a login session; set `bilibili_cookie.sessdata`.

**Can every video be read?** No. When the video or the part has no subtitles, the tool returns a clear "no subtitles" message.

**The cookie expired?** The tool reports that the login has expired; fetch a new SESSDATA, update the config, and reload the plugin.
## Changelog

> **[View changelog →](CHANGELOG.md)**

## Support & Acknowledgements

If this plugin helps you, please consider giving it a Star. For issues and suggestions, open an [Issue](https://github.com/OMSociety/astrbot_plugin_bilicaption/issues) or a [Pull Request](https://github.com/OMSociety/astrbot_plugin_bilicaption/pulls).

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) open-source chatbot framework
- [SodaCodeSave/astrbot_plugin_biliread](https://github.com/SodaCodeSave/astrbot_plugin_biliread) upstream plugin (AGPL-3.0)

## License & Author

This project is licensed under **AGPL-3.0** (inherited from the upstream BiliRead).

[@OMSociety](https://github.com/OMSociety)

