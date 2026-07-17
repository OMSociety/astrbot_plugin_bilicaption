"""
Bilicaption 核心逻辑测试

测试字幕格式化、配置校验等不依赖网络的核心功能。
"""

import json
import sys
import os
from typing import Optional

import pytest

# 将被测试模块加入路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ---------- 模拟字幕格式化逻辑 ----------


def format_subtitle(subtitle_list: list[dict], max_length: int = 0) -> str:
    """格式化字幕列表为纯文本（从 main.py 提取的核心逻辑）

    Args:
        subtitle_list: 字幕列表，每项含 content 和 timestamp 等字段
        max_length: 最大字符数，0 表示不限制

    Returns:
        格式化后的字幕纯文本
    """
    if not subtitle_list:
        return ""

    lines = []
    for sub in subtitle_list:
        content = sub.get("content", "").strip()
        if content:
            # 清理 HTML 标签
            content = content.replace("<br>", "\n").replace("</br>", "")
            lines.append(content)

    text = "\n".join(lines)

    if max_length > 0 and len(text) > max_length:
        text = text[:max_length] + "\n\n（字幕过长，已截断）"

    return text


def parse_subtitle_response(api_result: dict) -> tuple[Optional[list[dict]], Optional[str]]:
    """解析 B 站 API 返回的字幕数据（从 main.py 提取的核心逻辑）

    Args:
        api_result: B 站 API 返回的字幕 JSON

    Returns:
        (subtitle_list, error_msg) 元组
    """
    try:
        subtitle_data = api_result.get("data", {})
        if not subtitle_data:
            return None, "字幕数据为空"

        # B 站字幕返回格式：data.subtitle.subtitles[] 或 data.subtitle_list[]
        subtitles_raw = subtitle_data.get("subtitle", {}).get("subtitles", [])
        if not subtitles_raw:
            subtitles_raw = subtitle_data.get("subtitle_list", [])

        if not subtitles_raw:
            return None, "未找到字幕信息"

        return subtitles_raw, None

    except (AttributeError, TypeError, ValueError) as e:
        return None, f"解析字幕数据失败: {e}"


# ---------- 测试用例 ----------


class TestFormatSubtitle:
    """字幕格式化测试"""

    def test_empty_list(self):
        """空列表应返回空字符串"""
        assert format_subtitle([]) == ""

    def test_single_line(self):
        """单条字幕"""
        subs = [{"content": "你好世界", "timestamp": 0}]
        assert format_subtitle(subs) == "你好世界"

    def test_multiple_lines(self):
        """多条字幕"""
        subs = [
            {"content": "第一行", "timestamp": 0},
            {"content": "第二行", "timestamp": 1000},
            {"content": "第三行", "timestamp": 2000},
        ]
        result = format_subtitle(subs)
        assert result == "第一行\n第二行\n第三行"

    def test_html_br_cleaned(self):
        """HTML <br> 标签应替换为换行"""
        subs = [{"content": "第一行<br>第二行", "timestamp": 0}]
        assert format_subtitle(subs) == "第一行\n第二行"

    def test_max_length_cutoff(self):
        """设置最大长度时应截断"""
        subs = [{"content": "A" * 100}]
        result = format_subtitle(subs, max_length=10)
        assert len(result) < 50
        assert "截断" in result

    def test_max_length_zero(self):
        """max_length=0 时不截断"""
        subs = [{"content": "A" * 10000}]
        result = format_subtitle(subs, max_length=0)
        assert len(result) == 10000

    def test_skip_blank_content(self):
        """空 content 应跳过"""
        subs = [
            {"content": "", "timestamp": 0},
            {"content": "  ", "timestamp": 1000},
            {"content": "有效内容", "timestamp": 2000},
        ]
        assert format_subtitle(subs) == "有效内容"


class TestParseSubtitleResponse:
    """字幕 API 返回结果解析测试"""

    def test_valid_subtitle_list(self):
        """标准返回格式"""
        result = {
            "data": {
                "subtitle": {
                    "subtitles": [
                        {"id": 1, "lan_doc": "中文（普通话）"},
                        {"id": 2, "lan_doc": "英文"},
                    ]
                }
            }
        }
        subs, err = parse_subtitle_response(result)
        assert err is None
        assert len(subs) == 2

    def test_empty_data(self):
        """空数据"""
        subs, err = parse_subtitle_response({"data": {}})
        assert subs is None
        assert err is not None

    def test_no_subtitle_key(self):
        """无字幕键"""
        subs, err = parse_subtitle_response({"data": {"title": "test"}})
        assert subs is None
        assert err is not None

    def test_no_data_key(self):
        """无 data 键"""
        subs, err = parse_subtitle_response({"code": -400})
        assert subs is None
        assert err is not None

    def test_malformed_response(self):
        """损坏的返回"""
        subs, err = parse_subtitle_response({"data": None})
        assert subs is None
        assert err is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
