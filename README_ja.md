<p align="center"><a href="README.md">中文</a> · <a href="README_en.md">English</a> · <a href="README_ru.md">Русский</a> · <strong>日本語</strong></p>

<div align="center">

<h1><img src="https://raw.githubusercontent.com/OMSociety/astrbot_plugin_bilicaption/main/logo.png" width="192" alt="BiliCaption Logo"><br>BiliCaption bilibili 字幕リーダー</h1>

**bilibili 動画の字幕読み取りアシスタント** —— 動画の理解と要約 · 字幕原文の取得 · 多様なリンク形式 · 長い字幕のページ送り · 結果キャッシュ

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/OMSociety/astrbot_plugin_bilicaption)
[![AstrBot](https://img.shields.io/badge/AstrBot-%E2%89%A5v4-green.svg)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/license-AGPL--3.0-orange.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/OMSociety/astrbot_plugin_bilicaption)](https://github.com/OMSociety/astrbot_plugin_bilicaption/stargazers)
[![Issues](https://img.shields.io/github/issues/OMSociety/astrbot_plugin_bilicaption)](https://github.com/OMSociety/astrbot_plugin_bilicaption/issues)

</div>

> 本プロジェクトは AI が作成 · ソースコードは [SodaCodeSave/astrbot_plugin_biliread](https://github.com/SodaCodeSave/astrbot_plugin_biliread) をベースに二次開発

---

## 特長

| 特長 | 説明 |
|---|---|
| **動画を理解する `bili_view`** | 字幕を読み取り、ボットが動画を理解・要約・評価できるようにします。既定は 1 回 20000 文字で、長い場合は先頭と末尾を残し、残りは `offset` で読み進められます |
| **字幕原文 `bili_caption`** | 長さ無制限で字幕全文を返します。字幕を txt ファイルにしてチャットへ送ることもできます |
| **多様なリンク形式** | BV 番号 / av 番号 / 完全なリンク / b23.tv・bili2233.cn 短縮リンク / 共有テキスト全体。`?p=N` でパートを自動判別します |
| **結果キャッシュ** | 2 つのツールで共有し、既定は 1 時間・64 件。ページ送りで再リクエストしません |
| **明確な失敗理由** | 動画なし、字幕なし、ログイン失効、リスク制御、ネットワークタイムアウトを個別に通知します |

## ツールの使い分け

| ユーザーの要望 | ツール |
|:----|:----|
| 動画の理解・要約・評価、内容に関する質問への回答 | `bili_view` |
| 字幕テキストそのもの、または字幕の txt ファイル | `bili_caption` |

---

## クイックスタート

1. インストール：AstrBot WebUI → プラグインマーケット → `bilicaption` を検索。依存関係（bilibili-api-python 17.x / aiohttp / aiofiles）は `requirements.txt` から自動で入ります。
2. Cookie の設定（必須）：Bilibili の字幕 API にはログイン状態が必要です。`bilibili_cookie` グループに `sessdata`（[bilibili.com](https://www.bilibili.com) にログイン → F12 → Application → Cookies → `SESSDATA` の値をコピー）を入力し、必要なら `bili_jct` も入力します。
3. WebUI でプラグインを再読み込みし、チャットに Bilibili のリンクを送ります。

## 設定項目

| 項目 | 型 | 既定値 | 説明 |
|:------|:-----|:-------|:-----|
| `bilibili_cookie.sessdata` | string | `""` | Bilibili の SESSDATA Cookie（必須） |
| `bilibili_cookie.bili_jct` | string | `""` | Bilibili の bili_jct Cookie |
| `view_max_chars` | int | `20000` | `bili_view` が 1 回に返す最大文字数。`0` で無制限 |
| `auto_send_txt` | bool | `false` | 有効にすると `bili_caption` が字幕の txt ファイルをチャットへ送信します |
| `cache_ttl_seconds` | int | `3600` | 字幕キャッシュの有効期間（秒）。`0` でキャッシュ無効 |
| `cache_max_entries` | int | `64` | キャッシュの最大件数。超過時は最も長く使われていない項目を破棄します |

## ツール

### bili_view

| パラメータ | 型 | 必須 | 説明 |
|:----|:----|:----:|:-----|
| `video` | string | はい | BV 番号 / av 番号 / 完全なリンク / 短縮リンク / リンクを含む共有テキスト |
| `page` | integer | いいえ | 1 から始まるパート番号。リンクに `?p=N` があれば省略可 |
| `offset` | integer | いいえ | 結果に続きがあると示されたとき、この文字位置から読み進めます |

字幕が `view_max_chars` を超える場合、結果は先頭 60% と末尾 40% を残し、総文字数・省略割合・利用できる `offset` を示します。

### bili_caption

| パラメータ | 型 | 必須 | 説明 |
|:----|:----|:----:|:-----|
| `video` | string | はい | 上と同じ |
| `page` | integer | いいえ | 1 から始まるパート番号 |

## よくある質問

**設定は必要ですか？** はい。字幕 API にはログイン状態が必要なので、`bilibili_cookie.sessdata` を設定してください。

**すべての動画を読めますか？** いいえ。動画またはそのパートに字幕がない場合、ツールは「字幕なし」と明示して返します。

**Cookie が失効したら？** ログイン失効が通知されます。新しい SESSDATA を取得して設定を更新し、プラグインを再読み込みしてください。
## 更新履歴

> **[更新履歴を見る →](CHANGELOG.md)**

## 応援と謝辞

このプラグインが役に立ったら、Star をぜひお願いします。問題や提案があれば [Issue](https://github.com/OMSociety/astrbot_plugin_bilicaption/issues) または [Pull Request](https://github.com/OMSociety/astrbot_plugin_bilicaption/pulls) を提出してください。

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) オープンソースのチャットボットフレームワーク
- [SodaCodeSave/astrbot_plugin_biliread](https://github.com/SodaCodeSave/astrbot_plugin_biliread) フォーク元プラグイン（AGPL-3.0）

## ライセンスと作者

本プロジェクトは **AGPL-3.0** で公開されています（フォーク元の BiliRead を継承）。

[@OMSociety](https://github.com/OMSociety)

