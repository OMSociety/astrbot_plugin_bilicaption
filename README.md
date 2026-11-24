<p align="center"><strong>中文</strong> · <a href="README_en.md">English</a> · <a href="README_ru.md">Русский</a> · <a href="README_ja.md">日本語</a></p>

<div align="center">

<h1><img src="https://raw.githubusercontent.com/OMSociety/astrbot_plugin_bilicaption/main/logo.png" width="192" alt="BiliCaption Logo"><br>BiliCaption B站视频字幕解读</h1>

**B 站视频字幕读取助手** —— 理解与总结视频 · 字幕原文提取 · 多种链接格式 · 长字幕翻页 · 结果缓存

[![Version](https://img.shields.io/github/v/tag/OMSociety/astrbot_plugin_bilicaption?label=version&color=blue)](https://github.com/OMSociety/astrbot_plugin_bilicaption)
[![AstrBot](https://img.shields.io/badge/AstrBot-%E2%89%A5v4-green.svg)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/license-AGPL--3.0-orange.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/OMSociety/astrbot_plugin_bilicaption)](https://github.com/OMSociety/astrbot_plugin_bilicaption/stargazers)
[![Issues](https://img.shields.io/github/issues/OMSociety/astrbot_plugin_bilicaption)](https://github.com/OMSociety/astrbot_plugin_bilicaption/issues)

[核心特性](#核心特性) • [功能概览](#功能概览) • [快速开始](#快速开始) • [配置项说明](#配置项说明) • [LLM 可调用工具](#llm-可调用工具) • [常见问题](#常见问题) • [更新日志](CHANGELOG.md)

</div>

> 本项目由 AI 编写 · 源码基于 [SodaCodeSave/astrbot_plugin_biliread](https://github.com/SodaCodeSave/astrbot_plugin_biliread) 二次开发

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **理解视频 `bili_view`** | 读取字幕供 bot 理解、总结、评价视频；默认单次 20000 字，超长时保留开头与结尾并可用 `offset` 翻页 |
| **字幕原文 `bili_caption`** | 返回完整字幕，不限长度；可选把字幕保存为 txt 文件发到聊天 |
| **多种链接格式** | BV 号 / av 号 / 完整链接 / b23.tv 与 bili2233.cn 短链 / 整段分享文本，`?p=N` 自动识别分 P |
| **结果缓存** | 两个工具共用，默认 1 小时、64 条，翻页不重复请求 |
| **明确的失败原因** | 视频不存在、没有字幕、登录失效、风控、网络超时等分别给出具体提示 |

---

## 两个工具的分工

| 用户想要 | 工具 |
|:----|:----|
| 理解、总结、评价视频，或回答关于视频内容的问题 | `bili_view` |
| 字幕文本本身，或字幕 txt 文件 | `bili_caption` |

---
## 快速开始

### 第一步：安装

AstrBot WebUI → 插件市场 → 搜索 `bilicaption`

> **提示**：插件安装时会自动读取 `requirements.txt` 安装依赖（bilibili-api-python 17.x / aiohttp / aiofiles），无需手动安装。

### 第二步：配置 B 站 Cookie（必需）

> **提示**：B 站字幕接口需要登录态，**不配置 Cookie 无法获取字幕**（AI 字幕对匿名用户隐藏）。请先配置再使用。

在插件配置的 `bilibili_cookie` 分组中填写：

| 字段 | 获取方式 |
|:----|:----|
| `sessdata` | 浏览器登录 [bilibili.com](https://www.bilibili.com) → F12 → Application → Cookies → 复制 `SESSDATA` 的值 |
| `bili_jct` | 同上，复制 `bili_jct` 的值（可留空） |

### 第三步：重启生效

配置完成后在 WebUI 重载插件（或重启 AstrBot），即可在对话中发送 B 站链接测试。

---

## 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|:------|:-----|:-------|:-----|
| `bilibili_cookie.sessdata` | string | `""` | B 站 SESSDATA Cookie（必需，字幕接口需要登录态） |
| `bilibili_cookie.bili_jct` | string | `""` | B 站 bili_jct Cookie |
| `subtitle_language` | string | `zh` | 优先选用的字幕语言（语言代码前缀）；同语言内优先人工字幕 |
| `view_max_chars` | int | `20000` | `bili_view` 单次返回的字幕最大字符数，`0` 表示不限制 |
| `auto_send_txt` | bool | `false` | 开启后 `bili_caption` 自动发送字幕 txt 文件到聊天 |
| `cache_ttl_seconds` | int | `3600` | 字幕缓存有效期（秒），`0` 关闭缓存 |
| `cache_max_entries` | int | `64` | 缓存最大条数，超出淘汰最久未使用的条目 |

### 配置示例（`data/config/astrbot_plugin_bilicaption_config.json`）

```json
{
  "bilibili_cookie": {
    "sessdata": "你的SESSDATA",
    "bili_jct": "你的bili_jct"
  },
  "view_max_chars": 20000,
  "auto_send_txt": false,
  "cache_ttl_seconds": 3600,
  "cache_max_entries": 64
}
```

---

## LLM 可调用工具

模型自动判断何时调用，你只需用自然语言说需求：

```
用户: 总结一下这个视频 BV1GJ411x7h7
bot → bili_view(video=BV1GJ411x7h7)

用户: 把这个视频的字幕发我 https://b23.tv/4bdIZBf
bot → bili_caption(video=https://b23.tv/4bdIZBf)
```

### bili_view

| 参数 | 类型 | 必填 | 说明 |
|:----|:----|:----:|:-----|
| `video` | string | 是 | BV 号 / av 号 / 完整链接 / 短链 / 含链接的分享文本 |
| `page` | integer | 否 | 分 P 号，从 1 开始；链接已带 `?p=N` 时可省略 |
| `offset` | integer | 否 | 从该字符位置起继续读取；结果提示可继续读取时使用 |

字幕超过 `view_max_chars` 时，结果保留开头 60% 与结尾 40%，并给出总长、省略比例与可用的 `offset`。

### bili_caption

| 参数 | 类型 | 必填 | 说明 |
|:----|:----|:----:|:-----|
| `video` | string | 是 | 同上 |
| `page` | integer | 否 | 分 P 号，从 1 开始 |

---

## 常见问题

### Q1：需要配置吗？

需要。B 站字幕接口要求登录态，请配置 `bilibili_cookie.sessdata`（获取方式见[快速开始](#快速开始)）。

### Q2：所有视频都能获取字幕吗？

不是。该视频或该分 P 没有字幕时，工具会明确返回「没有字幕」。

### Q3：Cookie 失效怎么办？

工具会提示登录状态已失效，重新获取 SESSDATA 填入配置并重载插件即可。

### Q4：跟 BiliRead 有什么区别？

BiliRead 调用第三方 LLM 总结字幕；本插件直接返回字幕，由当前对话的 bot 自己理解或总结。
## 更新日志

> **[查看更新日志 →](CHANGELOG.md)**

## 支持与致谢

如果这个插件对你有帮助，欢迎点亮 Star，有问题和建议请提交 [Issue](https://github.com/OMSociety/astrbot_plugin_bilicaption/issues) 或 [Pull Request](https://github.com/OMSociety/astrbot_plugin_bilicaption/pulls)。

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) 开源聊天机器人框架
- [SodaCodeSave/astrbot_plugin_biliread](https://github.com/SodaCodeSave/astrbot_plugin_biliread) 上游插件（AGPL-3.0）

## 许可证与作者

本项目采用 **AGPL-3.0** 开源协议（继承上游 BiliRead）。

[@OMSociety](https://github.com/OMSociety)

