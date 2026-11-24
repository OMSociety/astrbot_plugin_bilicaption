<p align="center"><a href="README.md">中文</a> · <a href="README_en.md">English</a> · <strong>Русский</strong> · <a href="README_ja.md">日本語</a></p>

<div align="center">

<h1><img src="https://raw.githubusercontent.com/OMSociety/astrbot_plugin_bilicaption/main/logo.png" width="192" alt="BiliCaption Logo"><br>BiliCaption Чтение субтитров bilibili</h1>

**Помощник по чтению субтитров видео bilibili** —— понимание и краткий пересказ видео · исходный текст субтитров · разные форматы ссылок · постраничное чтение длинных субтитров · кэш результатов

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/OMSociety/astrbot_plugin_bilicaption)
[![AstrBot](https://img.shields.io/badge/AstrBot-%E2%89%A5v4-green.svg)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/license-AGPL--3.0-orange.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/OMSociety/astrbot_plugin_bilicaption)](https://github.com/OMSociety/astrbot_plugin_bilicaption/stargazers)
[![Issues](https://img.shields.io/github/issues/OMSociety/astrbot_plugin_bilicaption)](https://github.com/OMSociety/astrbot_plugin_bilicaption/issues)

</div>

> Проект написан с помощью ИИ · Исходный код основан на [SodaCodeSave/astrbot_plugin_biliread](https://github.com/SodaCodeSave/astrbot_plugin_biliread)

---

## Возможности

| Возможность | Описание |
|---|---|
| **Понимание видео: `bili_view`** | Читает субтитры, чтобы бот понял, пересказал или оценил видео; по умолчанию 20000 символов за вызов, у длинных субтитров сохраняются начало и конец, остальное читается через `offset` |
| **Исходные субтитры: `bili_caption`** | Возвращает полные субтитры без ограничения длины; может сохранить их в txt-файл и отправить в чат |
| **Разные форматы ссылок** | BV-код / номер av / полная ссылка / короткие ссылки b23.tv и bili2233.cn / целый текст «поделиться»; `?p=N` выбирает часть автоматически |
| **Кэш результатов** | Общий для обоих инструментов, по умолчанию 1 час и 64 записи; постраничное чтение не повторяет запросы |
| **Понятные причины ошибок** | Видео не найдено, нет субтитров, вход устарел, ограничение платформы, тайм-аут сети — каждый случай с отдельным сообщением |

## Какой инструмент

| Что нужно пользователю | Инструмент |
|:----|:----|
| Понять, пересказать или оценить видео, ответить на вопрос о его содержании | `bili_view` |
| Сам текст субтитров или txt-файл с ними | `bili_caption` |

---

## Быстрый старт

1. Установка: WebUI AstrBot → Магазин плагинов → поиск `bilicaption`. Зависимости (bilibili-api-python 17.x / aiohttp / aiofiles) ставятся из `requirements.txt` автоматически.
2. Cookie (обязательно): API субтитров Bilibili требует вход в аккаунт. В группе `bilibili_cookie` укажите `sessdata` (войдите на [bilibili.com](https://www.bilibili.com) → F12 → Application → Cookies → скопируйте значение `SESSDATA`), при желании также `bili_jct`.
3. Перезагрузите плагин в WebUI и отправьте в чат ссылку Bilibili.

## Настройки

| Параметр | Тип | По умолчанию | Описание |
|:------|:-----|:-------|:-----|
| `bilibili_cookie.sessdata` | string | `""` | Cookie SESSDATA Bilibili (обязательно) |
| `bilibili_cookie.bili_jct` | string | `""` | Cookie bili_jct Bilibili |
| `subtitle_language` | string | `zh` | Предпочитаемый язык субтитров (префикс кода языка); в пределах языка сначала ручные |
| `view_max_chars` | int | `20000` | Максимум символов за вызов `bili_view`; `0` — без ограничения |
| `auto_send_txt` | bool | `false` | Если включено, `bili_caption` отправляет txt-файл с субтитрами в чат |
| `cache_ttl_seconds` | int | `3600` | Время жизни кэша субтитров в секундах; `0` отключает кэш |
| `cache_max_entries` | int | `64` | Максимум записей в кэше; при превышении удаляется наименее недавно использованная |

## Инструменты

### bili_view

| Параметр | Тип | Обязателен | Описание |
|:----|:----|:----:|:-----|
| `video` | string | Да | BV-код / номер av / полная ссылка / короткая ссылка / текст со ссылкой |
| `page` | integer | Нет | Номер части с 1; можно опустить, если в ссылке есть `?p=N` |
| `offset` | integer | Нет | Продолжить чтение с этой позиции, когда в результате указано, что есть продолжение |

Если субтитры длиннее `view_max_chars`, в результате остаются первые 60% и последние 40%, а также указываются общая длина, доля пропущенного и подходящий `offset`.

### bili_caption

| Параметр | Тип | Обязателен | Описание |
|:----|:----|:----:|:-----|
| `video` | string | Да | Как выше |
| `page` | integer | Нет | Номер части с 1 |

## Вопросы и ответы

**Нужна ли настройка?** Да. API субтитров требует вход в аккаунт; укажите `bilibili_cookie.sessdata`.

**Можно ли прочитать любое видео?** Нет. Если у видео или части нет субтитров, инструмент прямо сообщает об этом.

**Cookie устарел?** Инструмент сообщит, что вход устарел; получите новый SESSDATA, обновите настройки и перезагрузите плагин.
## Список изменений

> **[Открыть список изменений →](CHANGELOG.md)**

## Поддержка и благодарности

Если плагин оказался полезен, поставьте ему Star. Вопросы и предложения создавайте [Issue](https://github.com/OMSociety/astrbot_plugin_bilicaption/issues) или отправляйте [Pull Request](https://github.com/OMSociety/astrbot_plugin_bilicaption/pulls).

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) фреймворк чат-ботов с открытым исходным кодом
- [SodaCodeSave/astrbot_plugin_biliread](https://github.com/SodaCodeSave/astrbot_plugin_biliread) исходный плагин (AGPL-3.0)

## Лицензия и автор

Проект распространяется по лицензии **AGPL-3.0** (унаследована от исходного BiliRead).

[@OMSociety](https://github.com/OMSociety)

