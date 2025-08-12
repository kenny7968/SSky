#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
URL関連ユーティリティの単体テスト
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import logging

from utils.url_utils import (
    extract_urls,
    open_url,
    extract_urls_from_facets,
    handle_urls_in_text,
    URL_PATTERN
)


class TestExtractUrls:
    """URL抽出機能のテスト"""
    
    def test_extract_urls_basic_https(self):
        """基本的なhttps URLの抽出テスト"""
        text = "Visit https://example.com for more info"
        urls = extract_urls(text)
        assert len(urls) == 1
        assert urls[0] == "https://example.com"
    
    def test_extract_urls_basic_http(self):
        """基本的なhttp URLの抽出テスト"""
        text = "Check out http://test.com/path"
        urls = extract_urls(text)
        assert len(urls) == 1
        assert urls[0] == "http://test.com/path"
    
    def test_extract_urls_www_prefix(self):
        """www プレフィックス付きURLの抽出テスト"""
        text = "Go to www.example.com"
        urls = extract_urls(text)
        assert len(urls) == 1
        assert urls[0] == "www.example.com"
    
    def test_extract_urls_multiple(self):
        """複数URL抽出のテスト"""
        text = "Visit https://site1.com and www.site2.com"
        urls = extract_urls(text)
        assert len(urls) == 2
        assert "https://site1.com" in urls
        assert "www.site2.com" in urls
    
    def test_extract_urls_with_paths(self):
        """パス付きURL抽出のテスト"""
        text = "Check https://example.com/path/to/page?param=value#section"
        urls = extract_urls(text)
        assert len(urls) == 1
        assert urls[0] == "https://example.com/path/to/page?param=value#section"
    
    def test_extract_urls_empty_text(self):
        """空文字列のテスト"""
        assert extract_urls("") == []
        assert extract_urls(None) == []
    
    def test_extract_urls_no_urls(self):
        """URLが含まれていないテキストのテスト"""
        text = "This is just regular text with no URLs"
        urls = extract_urls(text)
        assert len(urls) == 0
    
    def test_extract_urls_complex_text(self):
        """複雑なテキスト内のURL抽出テスト"""
        text = """
        Here are some links:
        1. https://github.com/user/repo
        2. www.stackoverflow.com/questions/123
        3. http://localhost:8080/api/v1/data
        Regular text here...
        """
        urls = extract_urls(text)
        assert len(urls) == 3
        assert "https://github.com/user/repo" in urls
        assert "www.stackoverflow.com/questions/123" in urls
        assert "http://localhost:8080/api/v1/data" in urls


class TestOpenUrl:
    """URL開く機能のテスト"""
    
    @patch('utils.url_utils.webbrowser')
    @patch('utils.url_utils.logger')
    def test_open_url_https_success(self, mock_logger, mock_webbrowser):
        """https URLを正常に開くテスト"""
        url = "https://example.com"
        result = open_url(url)
        
        assert result is True
        mock_webbrowser.open.assert_called_once_with(url)
        mock_logger.info.assert_called_once_with(f"URLを開きます: {url}")
    
    @patch('utils.url_utils.webbrowser')
    @patch('utils.url_utils.logger')
    def test_open_url_www_prefix(self, mock_logger, mock_webbrowser):
        """www プレフィックス付きURLの変換テスト"""
        url = "www.example.com"
        result = open_url(url)
        
        assert result is True
        expected_url = "https://www.example.com"
        mock_webbrowser.open.assert_called_once_with(expected_url)
        mock_logger.info.assert_called_once_with(f"URLを開きます: {expected_url}")
    
    @patch('utils.url_utils.wx')
    @patch('utils.url_utils.webbrowser')
    @patch('utils.url_utils.logger')
    def test_open_url_exception(self, mock_logger, mock_webbrowser, mock_wx):
        """URL開く際の例外処理テスト"""
        url = "https://example.com"
        test_exception = Exception("Browser not found")
        mock_webbrowser.open.side_effect = test_exception
        
        result = open_url(url)
        
        assert result is False
        mock_logger.error.assert_called_once_with(f"URLを開けませんでした: {str(test_exception)}")
        mock_wx.MessageBox.assert_called_once()


class TestExtractUrlsFromFacets:
    """facetsからのURL抽出テスト"""
    
    def test_extract_urls_from_facets_empty(self):
        """空のfacetsのテスト"""
        assert extract_urls_from_facets([]) == []
        assert extract_urls_from_facets(None) == []
    
    def test_extract_urls_from_facets_with_link_feature(self):
        """リンクfeature付きfacetsのテスト"""
        # Bluesky API形式のfacet オブジェクトをモック
        mock_feature = Mock()
        # __dict__に$typeを設定
        mock_feature.__dict__['$type'] = 'app.bsky.richtext.facet#link'
        mock_feature.uri = 'https://example.com'
        
        mock_facet = Mock()
        mock_facet.features = [mock_feature]
        
        facets = [mock_facet]
        urls = extract_urls_from_facets(facets)
        
        assert len(urls) == 1
        assert urls[0] == 'https://example.com'
    
    def test_extract_urls_from_facets_alternative_format(self):
        """代替形式のfacetsのテスト"""
        # uriプロパティのみを持つfeature
        mock_feature = Mock()
        mock_feature.uri = 'https://alt-example.com'
        # $type属性がない場合の代替チェック
        
        mock_facet = Mock()
        mock_facet.features = [mock_feature]
        
        facets = [mock_facet]
        urls = extract_urls_from_facets(facets)
        
        assert len(urls) == 1
        assert urls[0] == 'https://alt-example.com'
    
    def test_extract_urls_from_facets_multiple_features(self):
        """複数feature付きfacetsのテスト"""
        # 最初のfeature
        mock_feature1 = Mock()
        mock_feature1.__dict__['$type'] = 'app.bsky.richtext.facet#link'
        mock_feature1.uri = 'https://site1.com'
        
        # 2番目のfeature
        mock_feature2 = Mock()
        mock_feature2.__dict__['$type'] = 'app.bsky.richtext.facet#link'
        mock_feature2.uri = 'https://site2.com'
        
        mock_facet = Mock()
        mock_facet.features = [mock_feature1, mock_feature2]
        
        facets = [mock_facet]
        urls = extract_urls_from_facets(facets)
        
        assert len(urls) == 2
        assert 'https://site1.com' in urls
        assert 'https://site2.com' in urls
    
    def test_extract_urls_from_facets_no_features(self):
        """featuresプロパティがないfacetのテスト"""
        mock_facet = Mock()
        del mock_facet.features  # featuresプロパティを削除
        
        facets = [mock_facet]
        urls = extract_urls_from_facets(facets)
        
        assert len(urls) == 0
    
    @patch('utils.url_utils.logger')
    def test_extract_urls_from_facets_exception(self, mock_logger):
        """facets処理中の例外テスト"""
        # 例外を発生させるfacet
        mock_facet = Mock()
        mock_facet.features = Mock(side_effect=Exception("Facet processing error"))
        
        facets = [mock_facet]
        urls = extract_urls_from_facets(facets)
        
        assert len(urls) == 0
        mock_logger.error.assert_called_once()


class TestHandleUrlsInText:
    """テキスト内URL処理のテスト"""
    
    @patch('utils.url_utils.open_url')
    @patch('utils.url_utils.extract_urls_from_facets')
    def test_handle_urls_single_url_from_facets(self, mock_extract_facets, mock_open_url):
        """facetsから単一URL抽出・開くテスト"""
        mock_extract_facets.return_value = ['https://example.com']
        mock_open_url.return_value = True
        
        facets = [Mock()]  # モックfacets
        result = handle_urls_in_text("Some text", facets=facets)
        
        assert result is True
        mock_extract_facets.assert_called_once_with(facets)
        mock_open_url.assert_called_once_with('https://example.com')
    
    @patch('utils.url_utils.open_url')
    @patch('utils.url_utils.extract_urls')
    @patch('utils.url_utils.extract_urls_from_facets')
    def test_handle_urls_single_url_from_regex(self, mock_extract_facets, mock_extract_regex, mock_open_url):
        """正規表現から単一URL抽出・開くテスト"""
        mock_extract_facets.return_value = []  # facetsから見つからない
        mock_extract_regex.return_value = ['https://regex-found.com']
        mock_open_url.return_value = True
        
        result = handle_urls_in_text("Check https://regex-found.com")
        
        assert result is True
        mock_extract_regex.assert_called_once_with("Check https://regex-found.com")
        mock_open_url.assert_called_once_with('https://regex-found.com')
    
    @patch('utils.url_utils.wx')
    @patch('utils.url_utils.extract_urls')
    @patch('utils.url_utils.extract_urls_from_facets')
    def test_handle_urls_no_urls_found(self, mock_extract_facets, mock_extract_regex, mock_wx):
        """URLが見つからない場合のテスト"""
        mock_extract_facets.return_value = []
        mock_extract_regex.return_value = []
        
        mock_parent = Mock()
        result = handle_urls_in_text("No URLs here", parent=mock_parent)
        
        assert result is False
        mock_wx.MessageBox.assert_called_once_with(
            "URLが見つかりませんでした", "情報", mock_wx.OK | mock_wx.ICON_INFORMATION
        )
    
    @patch('utils.url_utils.open_url')
    @patch('utils.url_utils.wx')
    @patch('utils.url_utils.extract_urls')
    @patch('utils.url_utils.extract_urls_from_facets')
    def test_handle_urls_multiple_urls_dialog_ok(self, mock_extract_facets, mock_extract_regex, mock_wx, mock_open_url):
        """複数URL選択ダイアログでOKの場合のテスト"""
        mock_extract_facets.return_value = []
        mock_extract_regex.return_value = ['https://site1.com', 'https://site2.com']
        
        # モックダイアログ
        mock_dialog = Mock()
        mock_dialog.ShowModal.return_value = mock_wx.ID_OK
        mock_dialog.GetStringSelection.return_value = 'https://site2.com'
        mock_wx.SingleChoiceDialog.return_value = mock_dialog
        
        mock_open_url.return_value = True
        
        mock_parent = Mock()
        result = handle_urls_in_text("Multiple URLs", parent=mock_parent)
        
        assert result is True
        mock_wx.SingleChoiceDialog.assert_called_once()
        mock_dialog.ShowModal.assert_called_once()
        mock_dialog.GetStringSelection.assert_called_once()
        mock_dialog.Destroy.assert_called_once()
        mock_open_url.assert_called_once_with('https://site2.com')
    
    @patch('utils.url_utils.wx')
    @patch('utils.url_utils.extract_urls')
    @patch('utils.url_utils.extract_urls_from_facets')
    def test_handle_urls_multiple_urls_dialog_cancel(self, mock_extract_facets, mock_extract_regex, mock_wx):
        """複数URL選択ダイアログでキャンセルの場合のテスト"""
        mock_extract_facets.return_value = []
        mock_extract_regex.return_value = ['https://site1.com', 'https://site2.com']
        
        # モックダイアログ（キャンセル）
        mock_dialog = Mock()
        mock_dialog.ShowModal.return_value = mock_wx.ID_CANCEL
        mock_wx.SingleChoiceDialog.return_value = mock_dialog
        
        mock_parent = Mock()
        result = handle_urls_in_text("Multiple URLs", parent=mock_parent)
        
        assert result is False
        mock_dialog.ShowModal.assert_called_once()
        mock_dialog.Destroy.assert_called_once()
    
    @patch('utils.url_utils.extract_urls')
    @patch('utils.url_utils.extract_urls_from_facets')
    def test_handle_urls_multiple_urls_no_parent(self, mock_extract_facets, mock_extract_regex):
        """複数URLだが親ウィンドウがない場合のテスト"""
        mock_extract_facets.return_value = []
        mock_extract_regex.return_value = ['https://site1.com', 'https://site2.com']
        
        result = handle_urls_in_text("Multiple URLs", parent=None)
        
        assert result is False


class TestUrlPatternRegex:
    """URL正規表現パターンのテスト"""
    
    def test_url_pattern_direct_usage(self):
        """URL_PATTERNの直接使用テスト"""
        import re
        
        test_cases = [
            ("https://example.com", True),
            ("http://test.org", True),
            ("www.site.com", True),
            ("ftp://files.com", False),  # ftpは対象外
            ("mailto:test@example.com", False),  # mailtoは対象外
            ("just text", False),
        ]
        
        for text, should_match in test_cases:
            matches = re.findall(URL_PATTERN, text)
            if should_match:
                assert len(matches) > 0, f"'{text}' should match URL pattern"
            else:
                assert len(matches) == 0, f"'{text}' should not match URL pattern"


class TestUrlUtilsIntegration:
    """URL utilities統合テスト"""
    
    @patch('utils.url_utils.webbrowser')
    @patch('utils.url_utils.logger')
    def test_complete_url_workflow(self, mock_logger, mock_webbrowser):
        """完全なURLワークフローのテスト"""
        # テキストからURL抽出
        text = "Visit our site at https://example.com for details"
        urls = extract_urls(text)
        
        assert len(urls) == 1
        assert urls[0] == "https://example.com"
        
        # URL開く
        result = open_url(urls[0])
        
        assert result is True
        mock_webbrowser.open.assert_called_once_with("https://example.com")
    
    def test_url_detection_accuracy(self):
        """URL検出精度のテスト"""
        test_text = """
        正規のURL: https://github.com/user/repo
        www形式: www.stackoverflow.com
        パス付き: https://api.example.com/v1/data?key=value
        フラグメント付き: https://docs.site.com/page#section
        ポート番号付き: http://localhost:8080/app
        無効なもの: javascript:alert('xss')
        プレーンテキスト: これは普通のテキストです
        """
        
        urls = extract_urls(test_text)
        
        # 期待されるURL数
        assert len(urls) == 5
        
        # 検出されるべきURL
        expected_urls = [
            "https://github.com/user/repo",
            "www.stackoverflow.com",
            "https://api.example.com/v1/data?key=value",
            "https://docs.site.com/page#section",
            "http://localhost:8080/app"
        ]
        
        for expected_url in expected_urls:
            assert expected_url in urls, f"Expected URL '{expected_url}' not found"


class TestEdgeCasesAndErrorHandling:
    """エッジケースとエラーハンドリングのテスト"""
    
    def test_extract_urls_unicode_text(self):
        """Unicode文字を含むテキストのテスト"""
        text = "日本語のテキスト https://日本.example.com と english text www.test.org"
        urls = extract_urls(text)
        
        # 基本的なURLは検出されるはず
        assert "www.test.org" in urls
        # Unicode URLの扱いは実装依存
    
    def test_extract_urls_very_long_text(self):
        """非常に長いテキストのテスト"""
        base_text = "Check out https://example.com " * 1000
        urls = extract_urls(base_text)
        
        # 1000個のURLが検出されるはず
        assert len(urls) == 1000
        assert all(url == "https://example.com" for url in urls)
    
    def test_malformed_facets_handling(self):
        """不正な形式のfacetsのテスト"""
        # None値を含むfacets
        facets = [None, Mock()]
        
        # 例外を発生させずに処理されることを確認
        urls = extract_urls_from_facets(facets)
        assert isinstance(urls, list)
    
    @patch('utils.url_utils.logger')
    def test_logging_behavior(self, mock_logger):
        """ログ出力動作のテスト"""
        # 正常なURL開く操作
        with patch('utils.url_utils.webbrowser') as mock_webbrowser:
            open_url("https://test.com")
            mock_logger.info.assert_called()
        
        # エラー時のログ
        with patch('utils.url_utils.webbrowser') as mock_webbrowser, \
             patch('utils.url_utils.wx') as mock_wx:
            mock_webbrowser.open.side_effect = Exception("Test error")
            open_url("https://test.com")
            mock_logger.error.assert_called()