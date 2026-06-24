# server/tests/unit/test_tools.py
# 测试行为：
# - test_build_search_query_normal: 正常步骤信息 → 拼接包含 step_title + step_desc + 高一数学
# - test_build_search_query_truncation: 超长输入 → 截断到 80 字符以内
# - test_build_search_query_short: 短输入 → 不截断
# - test_search_resources_structure: mock 搜索 → 返回 list[dict] 含 title/url/snippet
# - test_search_resources_empty_on_error: mock 异常 → 返回空列表不抛异常
# - test_search_resources_import: tools 模块可导入

import pytest
from unittest.mock import patch, MagicMock


class TestBuildSearchQuery:
    def test_normal(self):
        """正常步骤信息 → 拼接包含关键信息"""
        from orchestrator.tools import build_search_query
        result = build_search_query("二次函数定义", "学习标准形式和基本概念")
        assert "二次函数定义" in result
        assert "标准形式" in result
        assert "高一数学" in result

    def test_truncation(self):
        """超长输入 → 截断到 80 字符"""
        from orchestrator.tools import build_search_query
        long_title = "这是一个非常非常长的步骤标题用来测试截断功能" * 5
        long_desc = "这是一个非常非常长的步骤描述用来测试截断功能" * 5
        result = build_search_query(long_title, long_desc)
        assert len(result) <= 80

    def test_short(self):
        """短输入 → 不截断"""
        from orchestrator.tools import build_search_query
        result = build_search_query("函数", "定义")
        assert len(result) == len("函数 定义 高一数学")


class TestSearchResources:
    def test_import(self):
        """tools 模块可导入"""
        from orchestrator import tools
        assert hasattr(tools, "search_resources")

    def test_returns_list_of_dicts(self):
        """mock 搜索 → 返回 list[dict] 含 title/url/snippet"""
        from orchestrator.tools import search_resources

        mock_results = [
            {"title": "二次函数入门", "href": "https://example.com/1", "body": "这是摘要1"},
            {"title": "二次函数图像", "href": "https://example.com/2", "body": "这是摘要2"},
        ]

        with patch("orchestrator.tools.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = mock_results
            mock_ddgs.return_value.__enter__.return_value = mock_instance

            results = search_resources("二次函数")

        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]["title"] == "二次函数入门"
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["snippet"] == "这是摘要1"

    def test_empty_on_exception(self):
        """mock 异常 → 返回空列表不抛异常"""
        from orchestrator.tools import search_resources

        with patch("orchestrator.tools.DDGS") as mock_ddgs:
            mock_ddgs.side_effect = Exception("网络错误")

            results = search_resources("二次函数")

        assert results == []
