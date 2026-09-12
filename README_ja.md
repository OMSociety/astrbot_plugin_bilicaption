<p align="center"><a href="README.md">中文</a> · <a href="README_en.md">English</a> · <a href="README_ru.md">Русский</a> · <strong>日本語</strong></p>

<div align="center">

<img src="https://raw.githubusercontent.com/OMSociety/astrbot_plugin_bilicaption/main/logo.png" width="120" alt="BiliCaption Logo" />

# 🎬 BiliCaption bilibili 字幕抽出・解読

**bilibili 動画の字幕抽出と深掘り解読アシスタント** —— 字幕テキスト抽出 · 字幕全文通読 · リンク自動判別 · 長さ制御 · txt ファイル送信

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/OMSociety/astrbot_plugin_bilicaption)
[![AstrBot](https://img.shields.io/badge/AstrBot-%E2%89%A5v4-green.svg)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/license-AGPL--3.0-orange.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/OMSociety/astrbot_plugin_bilicaption)](https://github.com/OMSociety/astrbot_plugin_bilicaption/stargazers)
[![Issues](https://img.shields.io/github/issues/OMSociety/astrbot_plugin_bilicaption)](https://github.com/OMSociety/astrbot_plugin_bilicaption/issues)

</div>

> 🎨 本プロジェクトは AI が作成 · ソースコードは [SodaCodeSave/astrbot_plugin_biliread](https://github.com/SodaCodeSave/astrbot_plugin_biliread) をベースに二次開発

---

## ✨ 主な特徴

| 特徴 | 説明 |
|------|------|
| 📝 **字幕テキスト抽出** | bilibili 動画の字幕原文を抽出し、AI による要約は行わず、そのままユーザーへ返します |
| 🧠 **字幕の深掘り通読** | 字幕全文を bot 自身に渡し、bot が動画内容を自ら解読・要約します（任意、トークン消費大） |
| 🔗 **リンク自動判別** | bilibili の完全なリンク / BV 番号 / b23.tv 短縮リンク / 裸の短縮コードに対応し、自動で解析します |
| ✂️ **長さ制御** | 2 つのツールそれぞれで字幕の最大文字数を設定でき、コンテキストの溢れを防ぎます |
| 📄 **txt ファイル送信** | 字幕全文を txt ファイルとして保存しチャットへ送ることができます（任意） |
| 🔒 **ログイン状態対応** | bilibili の Cookie を設定すると完全な AI 字幕を取得できます（字幕 API にはログイン状態が必要） |

---

## 📖 機能概要

### 字幕抽出 bilibili_caption
チャットで bilibili のリンク / BV 番号を送るだけで、bot が自動でツールを呼び出し、字幕テキストを返します。

### 深掘り解読 bilibili_read
有効にすると、動画の解読を求められたとき、bot はまず字幕全文を通読してから文章を組み立てます。

### 2 つのツールの違い

| 特徴 | `bilibili_caption` | `bilibili_read` |
|:----|:-------------------|:----------------|
| 位置づけ | 字幕原文をすばやく抽出 | bot 自身の読解のための深掘り解読 |
| 返却 | 字幕テキスト。AI がユーザーへ表示 | 字幕全文。bot の思考フローへ入力 |
| トークン消費 | 制御可能（切り詰め可） | やや大きい（既定では全文通読） |
| 既定で有効 | ✅ 常に利用可能 | ❌ 既定はオフ。設定での有効化が必要 |

---

## 🚀 クイックスタート

### ステップ 1: インストール

**方法 1: プラグインマーケット**
- AstrBot WebUI → プラグインマーケット → `bilicaption` を検索

**方法 2: GitHub リポジトリ**
- AstrBot WebUI → プラグイン管理 → ＋ インストール
- リポジトリ URL を貼り付け： `https://github.com/OMSociety/astrbot_plugin_bilicaption`

> 💡 プラグインのインストール時、依存パッケージ（bilibili-api-python / aiohttp / aiofiles）は `requirements.txt` に基づき自動でインストールされます。手動インストールは不要です。

### ステップ 2: bilibili の Cookie を設定（必須）

> 💡 bilibili の字幕 API にはログイン状態が必要で、**Cookie を設定しないと字幕を取得できません**（AI 字幕は匿名ユーザーには非表示です）。使用前に設定してください。

プラグイン設定の `bilibili_cookie` グループに入力します：

| 項目 | 取得方法 |
|:----|:----|
| `sessdata` | ブラウザで [bilibili.com](https://www.bilibili.com) にログイン → F12 → Application → Cookies → `SESSDATA` の値をコピー |
| `bili_jct` | 同様に `bili_jct` の値をコピー |

### ステップ 3: 再起動で反映

設定後、WebUI でプラグインを再読み込み（または AstrBot を再起動）し、チャットで bilibili のリンクを送ってテストできます。

---

## ⚙️ 設定項目の説明

| 設定項目 | 型 | 既定値 | 説明 |
|:------|:-----|:-------|:-----|
| `bilibili_cookie.sessdata` | string | `""` | bilibili の SESSDATA Cookie（必須。字幕 API にはログイン状態が必要） |
| `bilibili_cookie.bili_jct` | string | `""` | bilibili の bili_jct Cookie |
| `max_subtitle_length` | int | `0` | caption ツールの字幕最大文字数。`0` は無制限 |
| `auto_send_txt` | bool | `false` | 有効にすると、抽出した字幕を自動で txt ファイルとしてチャットへ送信 |
| `enable_read_tool` | bool | `false` | `bilibili_read` 深掘り解読ツールを有効化（トークン消費大） |
| `read_max_subtitle_length` | int | `0` | read ツールの字幕最大文字数。`0` は無制限（全文通読） |

### クイック設定テンプレート

WebUI の設定パネルに入力するか、次の構造を参考にしてください（`data/config/astrbot_plugin_bilicaption_config.json`：

```json
{
  "bilibili_cookie": {
    "sessdata": "你的SESSDATA",
    "bili_jct": "你的bili_jct"
  },
  "max_subtitle_length": 0,
  "auto_send_txt": false,
  "enable_read_tool": false,
  "read_max_subtitle_length": 0
}
```

---

## 🛠️ LLM が呼び出せるツール

プラグインは 2 つの LLM ツールを登録します（`bilibili_read` には設定 `enable_read_tool` の有効化が必要）。モデルが呼び出しタイミングを自動で判断するため、自然な言葉で要求するだけです：

```
用户: 帮我提取这个视频的字幕 https://b23.tv/4bdIZBf
🤖 → bilibili_caption(bvid=https://b23.tv/4bdIZBf)
    [字幕] 《人工智能发展简史：从图灵到 GPT》
    大家好，欢迎来到本期视频...

用户: 解读一下这个视频 BV1GJ411x7h7
🤖 → bilibili_read(bvid=BV1GJ411x7h7)
    （通读完整字幕后自行组织语言输出解读）
```

### bilibili_caption
bilibili 動画の字幕テキストを取得します。字幕がない場合はその旨のメッセージを返します。

| パラメータ | 型 | 必須 | 説明 |
|:----|:----|:----:|:-----|
| `bvid` | string | ✅ | BVID / bilibili の完全なリンク / b23.tv 短縮リンク。例: `BV1GJ411x7h7` または `https://b23.tv/4bdIZBf` |
| `page` | integer | ❌ | パート番号。1 から開始、既定は 1。単一パートの動画では指定不要 |

### bilibili_read（設定 `enable_read_tool` の有効化が必要）
bilibili 動画の字幕全文を通読し、bot が動画内容を解読できるようにします。ユーザーが bilibili 動画の要約・分析・評価を求めたときに呼び出されます。

| パラメータ | 型 | 必須 | 説明 |
|:----|:----|:----:|:-----|
| `bvid` | string | ✅ | BVID / bilibili の完全なリンク / b23.tv 短縮リンク |
| `page` | integer | ❌ | パート番号。1 から開始、既定は 1。単一パートの動画では指定不要 |

> 注意: `bilibili_read` は字幕原文を全文返すのみで、事前準備されたプロンプトは一切付加しません。bot が自身で読み、解読方法を判断します。

---

## ⚠️ よくある質問

### Q1：設定は必要ですか？

**必要です**。bilibili の字幕 API にはログイン状態が必要です。`bilibili_cookie.sessdata` と `bili_jct` を設定してください（取得方法は[クイックスタート](#-クイックスタート)参照）。

### Q2：すべての動画で字幕を取得できますか？

いいえ。UP 主が字幕をアップロードしておらず、bilibili に AI 字幕もない動画は内容を取得できません。その場合「現在利用できる字幕はありません」と表示されます。

### Q3：なぜ AI 要約をしないのですか？

`bilibili_caption` はもともと原文抽出に特化しています。`bilibili_read` は要約を bot 自身に任せ、事前準備されたプロンプトを使いません。

### Q4：`bilibili_caption` と `bilibili_read` の違いは何ですか？

caption は字幕テキストをすばやく返してあなたに見せます。read は全文を bot に渡し、bot 自身が通読してから解読を出力します。read はトークンを消費しますが、解読の質は高くなります。両者は代替関係ではなく、必要に応じてオン・オフを設定してください。

### Q5：BiliRead との違いは何ですか？

BiliRead はサードパーティの LLM を呼び出して字幕を要約します。本プラグインはサードパーティの LLM を介さず、字幕原文をそのまま返すか、現在の対話の bot 自身を使って解読します。

## 📝 更新履歴

> 📋 **[更新履歴を見る →](CHANGELOG.md)**

---

## ⭐ プロジェクトを支援

このプラグインが役に立ったら、Star ⭐ をぜひお願いします。問題や提案があれば [Issue](https://github.com/OMSociety/astrbot_plugin_bilicaption/issues) または [Pull Request](https://github.com/OMSociety/astrbot_plugin_bilicaption/pulls) を提出してください。

## 🙏 謝辞

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) オープンソースのチャットボットフレームワーク
- [SodaCodeSave/astrbot_plugin_biliread](https://github.com/SodaCodeSave/astrbot_plugin_biliread) フォーク元プラグイン（AGPL-3.0）

---

## 📜 ライセンス

本プロジェクトは **AGPL-3.0** で公開されています（フォーク元の BiliRead を継承）。

---

## 👤 作者

[@OMSociety](https://github.com/OMSociety)
