<div align="center">
    <img src="./logo.png">
    <h1>BiliCaption</h1>
    <p>AstrBot 插件，从B站视频中提取字幕纯文本，不做AI总结，直接输出原始字幕。</p>
</div>

## ✨ 功能特性

- 📝 **原始字幕输出**：获取 B 站视频的字幕纯文本，不经过任何 AI 总结或改写
- 🛠️ **LLM 工具集成**：以 Tool 形式注册，AI 对话中自动响应含 B 站链接/BV号的消息
- 🌐 **短链支持**：自动识别并解析 `b23.tv` 短链接
- 📏 **长度控制**：可配置字幕最大返回长度，防止上下文溢出

## 📦 安装

### 手动安装

```bash
cd data/plugins
git clone https://github.com/OMSociety/astrbot_plugin_bilicaption.git
```

重启 AstrBot 即可生效。

## ⚙️ 配置说明

进入 AstrBot 后台 → AstrBot 插件 → 找到 `BiliCaption`：

### 1. B站 Cookie

| 配置项 | 必填 | 说明 |
|--------|------|------|
| `sessdata` | 否 | B 站登录态 Cookie |
| `bili_jct` | 否 | B 站登录态 Cookie |

> 不配置 Cookie 也能工作，但部分视频的字幕可能无法获取。获取方式见原 README 中的教程。

### 2. 字幕最大返回长度

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `max_subtitle_length` | number | 0 | 字幕最大字符数，0 表示不限制 |

## 🚀 使用方法

本插件以 **Tool (LLM 工具)** 的形式运行，**无需发送特定指令**。

当你与 AstrBot 聊天时，发送包含 **B 站视频链接**、**BV 号** 或 **b23.tv 短链** 的消息，AI 会自动调用 `bilibili_caption` 工具来获取视频字幕纯文本。

### 示例

```
用户：这个视频讲啥的？BV1GJ411x7h7
→ AI 调用工具获取字幕，直接展示原始文本

用户：https://b23.tv/4bdIZBf 帮我看下字幕
→ 插件自动解析短链，提取字幕
```

## ⚠️ 注意事项 & 常见问题

1. **不是所有视频都有字幕**：UP 主未上传字幕且 B 站无 AI 字幕的视频无法获取内容
2. **字幕内容不做总结**：本插件仅提取字幕原文，AI 的回复风格取决于你当前使用的主模型
3. **Cookie 有效期**：SESSDATA 通常有效期为几个月，过期后需重新配置
4. **风控限制**：请求过于频繁可能触发 B 站风控

## 🔄 与 BiliRead 的区别

| 特性 | BiliRead | BiliCaption |
|------|----------|-------------|
| 输出内容 | LLM 总结后的理解 | 原始字幕文本 |
| 需配置总结模型 | 是（需指定 llm_provider_id） | 否 |
| 用途 | AI 用自己的话复述 | 直接展示字幕原文 |

## 📜 开源协议

AGPL-3.0 license

## 🙏 致谢

基于 [SodaCodeSave/astrbot_plugin_biliread](https://github.com/SodaCodeSave/astrbot_plugin_biliread) fork 改造，删除了 LLM 总结逻辑，改为直接输出字幕文本。
