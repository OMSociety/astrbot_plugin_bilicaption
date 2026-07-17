# BiliCaption - B站字幕提取

[![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)](https://github.com/OMSociety/astrbot_plugin_bilicaption)
[![AstrBot](https://img.shields.io/badge/AstrBot-%E2%89%A5v4-green.svg)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/license-AGPL--3.0-orange.svg)](LICENSE)

获取 B 站视频字幕纯文本，不做 AI 总结，直接返回原始字幕。以 LLM Tool 形式运行，自动响应含 B 站链接 / BV 号 / b23 短链的消息。

> 本项目由AI编写，部分源码基于 [SodaCodeSave/astrbot_plugin_biliread](https://github.com/SodaCodeSave/astrbot_plugin_biliread) 。

[快速开始](#-快速开始) • [配置项](#-配置项说明) • [LLM 工具](#-llm-可调用工具) • [常见问题](#-常见问题)

---

## 📖 功能概览

### 核心能力
- **原始字幕输出** — 提取 B 站视频字幕纯文本，不经过任何 AI 总结或改写
- **LLM 工具集成** — 以 Tool 形式注册，AI 对话中自动响应含 B 站链接 / BV 号的消息
- **短链支持** — 自动识别并解析 `b23.tv` 短链接
- **长度控制** — 可配置字幕最大返回长度，防止上下文溢出
- **txt 文件推送** — 可选将字幕保存为 txt 文件发送到聊天中

---

## 🚀 快速开始

### 安装

**方式一：插件市场**
- AstrBot WebUI → 插件市场 → 搜索 `bilicaption`

**方式二：GitHub 仓库**
- AstrBot WebUI → 插件管理 → ＋ 安装
- 粘贴仓库地址：`https://github.com/OMSociety/astrbot_plugin_bilicaption`

### 依赖安装
```bash
pip install -r requirements.txt
```
核心依赖：`bilibili-api-python`

---

## ⚙️ 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|:------|:-----|:-------|:-----|
| `bilibili_cookie.sessdata` | string | - | B 站 SESSDATA（可选，不配也能用但部分视频字幕受限） |
| `bilibili_cookie.bili_jct` | string | - | B 站 bili_jct（可选） |
| `max_subtitle_length` | number | `0` | 字幕最大字符数，`0` 表示不限制 |
| `auto_send_txt` | bool | `false` | 开启后每次提取字幕都会自动将字幕保存为 txt 文件并发送到聊天中 |

> 更多配置说明请参考[B站Cookie获取教程](https://github.com/SodaCodeSave/astrbot_plugin_biliread#1-b%E7%AB%99-cookie)。

---

## 🛠️ LLM 可调用工具

### bilibili_caption
获取哔哩哔哩视频的字幕纯文本。如果视频没有字幕则返回提示信息。

| 参数 | 类型 | 必填 | 说明 |
|:----|:----|:----:|:-----|
| `bvid` | string | ✅ | BVID 或 b23.tv 短链，例如 `BV1GJ411x7h7` 或 `https://b23.tv/4bdIZBf` |

**典型调用流程：**
1. 用户发送 B 站链接 / BV 号 / b23 短链
2. AI 自动调用 `bilibili_caption` 工具
3. 返回原始字幕文本，AI 直接展示给用户

---

## ⚠️ 常见问题

**Q：所有视频都能获取字幕吗？**
A：不是。UP 主未上传字幕且 B 站无 AI 字幕的视频无法获取内容。

**Q：为什么不做 AI 总结？**
A：本插件的定位就是「提取字幕原文」。AI 拿到原文后如何回复，取决于你当前使用的 LLM，不在此插件职责范围内。

**Q：需要配置吗？**
A：无需任何配置即可使用基础功能。如果需要获取部分需要登录态的字幕，建议配置 B 站 Cookie。

**Q：跟 BiliRead 有什么区别？**
A：BiliRead 会调用 LLM 总结字幕内容后输出；BiliCaption 跳过总结环节，直接返回字幕原文。且不需要额外配置总结模型。

---

## 📜 许可证

本项目采用 **AGPL-3.0** 开源协议（同步上游 BiliRead）。

---

## 👤 作者

**OMSociety** — [@OMSociety](https://github.com/OMSociety)
