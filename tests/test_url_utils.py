#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
URL関連ユーティリティのテスト
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.url_utils import extract_urls, open_url, extract_urls_from_facets, handle_urls_in_text

class TestUrlUtils(unittest.TestCase):
    """URL関連ユーティリティのテストクラス"""
    
    def test_extract_urls_https(self):
        """HTTPS URLの抽出テスト"""
        text = "こちらのサイトをご覧ください: https://example.com/path?param=value"
        urls = extract_urls(text)
        
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "https://example.com/path?param=value")
    
    def test_extract_urls_http(self):
        """HTTP URLの抽出テスト"""
        text = "HTTPサイト: http://example.com"
        urls = extract_urls(text)
        
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "http://example.com")
    
    def test_extract_urls_www(self):
        """www URLの抽出テスト"""
        text = "詳細は www.example.com をご確認ください"
        urls = extract_urls(text)
        
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "www.example.com")
    
    def test_extract_urls_multiple(self):
        """複数URLの抽出テスト"""
        text = "https://example.com と www.test.org と http://another.com をチェック"
        urls = extract_urls(text)
        
        self.assertEqual(len(urls), 3)
        self.assertIn("https://example.com", urls)
        self.assertIn("www.test.org", urls)
        self.assertIn("http://another.com", urls)
    
    def test_extract_urls_no_urls(self):
        """URLが含まれていないテキストのテスト"""
        text = "これはURLを含まないテキストです"
        urls = extract_urls(text)
        
        self.assertEqual(len(urls), 0)
    
    def test_extract_urls_empty_text(self):
        """空のテキストのテスト"""
        urls = extract_urls("")
        self.assertEqual(len(urls), 0)
        
        urls = extract_urls(None)
        self.assertEqual(len(urls), 0)
    
    def test_extract_urls_complex_path(self):
        """複雑なパスを持つURLの抽出テスト"""
        text = "API: https://api.example.com/v1/users?id=123&format=json#section"
        urls = extract_urls(text)
        
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "https://api.example.com/v1/users?id=123&format=json#section")
    
    @patch('utils.url_utils.webbrowser.open')
    def test_open_url_https(self, mock_open):
        """HTTPS URLを開くテスト"""
        url = "https://example.com"
        result = open_url(url)
        
        self.assertTrue(result)
        mock_open.assert_called_once_with(url)
    
    @patch('utils.url_utils.webbrowser.open')
    def test_open_url_www(self, mock_open):
        """www URLを開くテスト（https://が追加される）"""
        url = "www.example.com"
        result = open_url(url)
        
        self.assertTrue(result)
        mock_open.assert_called_once_with("https://www.example.com")
    
    @patch('utils.url_utils.webbrowser.open')
    @patch('utils.url_utils.wx.MessageBox')
    def test_open_url_error(self, mock_msgbox, mock_open):
        """URL開きエラーのテスト"""
        # webbrowser.openが例外を発生させる
        mock_open.side_effect = Exception("ブラウザエラー")
        
        url = "https://example.com"
        result = open_url(url)
        
        self.assertFalse(result)
        mock_msgbox.assert_called_once()
    
    def test_extract_urls_from_facets_empty(self):
        """空のfacetsからの抽出テスト"""
        urls = extract_urls_from_facets(None)
        self.assertEqual(len(urls), 0)
        
        urls = extract_urls_from_facets([])
        self.assertEqual(len(urls), 0)
    
    def test_extract_urls_from_facets_with_links(self):
        """リンクを含むfacetsからの抽出テスト"""
        # モックfacetオブジェクトを作成
        mock_feature = MagicMock()
        mock_feature.uri = "https://example.com"
        setattr(mock_feature, '$type', 'app.bsky.richtext.facet#link')
        
        mock_facet = MagicMock()
        mock_facet.features = [mock_feature]
        
        facets = [mock_facet]
        urls = extract_urls_from_facets(facets)
        
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "https://example.com")
    
    def test_extract_urls_from_facets_no_features(self):
        """featuresがないfacetsのテスト"""
        mock_facet = MagicMock()
        del mock_facet.features  # featuresプロパティを削除
        
        facets = [mock_facet]
        urls = extract_urls_from_facets(facets)
        
        self.assertEqual(len(urls), 0)
    
    def test_extract_urls_from_facets_alternative_format(self):
        """代替形式のfacetsからの抽出テスト"""
        # $typeがないがuriがあるfeature
        mock_feature = MagicMock()
        mock_feature.uri = "https://alternative.com"
        # $typeプロパティを削除
        if hasattr(mock_feature, '$type'):
            delattr(mock_feature, '$type')
        
        mock_facet = MagicMock()
        mock_facet.features = [mock_feature]
        
        facets = [mock_facet]
        urls = extract_urls_from_facets(facets)
        
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "https://alternative.com")
    
    @patch('utils.url_utils.open_url')
    def test_handle_urls_in_text_single_url(self, mock_open_url):
        """単一URLの処理テスト"""
        mock_open_url.return_value = True
        
        text = "チェックしてください: https://example.com"
        result = handle_urls_in_text(text)
        
        self.assertTrue(result)
        mock_open_url.assert_called_once_with("https://example.com")
    
    @patch('utils.url_utils.wx.MessageBox')
    def test_handle_urls_in_text_no_urls(self, mock_msgbox):
        """URLがないテキストの処理テスト"""
        mock_parent = MagicMock()
        
        text = "URLを含まないテキスト"
        result = handle_urls_in_text(text, parent=mock_parent)
        
        self.assertFalse(result)
        mock_msgbox.assert_called_once_with(
            "URLが見つかりませんでした", "情報", unittest.mock.ANY
        )
    
    @patch('utils.url_utils.open_url')
    @patch('utils.url_utils.wx.SingleChoiceDialog')
    def test_handle_urls_in_text_multiple_urls(self, mock_dialog, mock_open_url):
        """複数URLの処理テスト"""
        mock_open_url.return_value = True
        
        # ダイアログのモック設定
        mock_dlg = MagicMock()
        mock_dlg.ShowModal.return_value = 1  # wx.ID_OK
        mock_dlg.GetStringSelection.return_value = "https://example.com"
        mock_dialog.return_value = mock_dlg
        
        mock_parent = MagicMock()
        text = "https://example.com と https://test.org"
        result = handle_urls_in_text(text, parent=mock_parent)
        
        self.assertTrue(result)
        mock_dialog.assert_called_once()
        mock_open_url.assert_called_once_with("https://example.com")
    
    @patch('utils.url_utils.extract_urls_from_facets')
    @patch('utils.url_utils.open_url')
    def test_handle_urls_in_text_with_facets(self, mock_open_url, mock_extract_facets):
        """facetsを使用したURL処理テスト"""
        mock_open_url.return_value = True
        mock_extract_facets.return_value = ["https://facet-url.com"]
        
        text = "テキスト内のURL: https://text-url.com"
        facets = [MagicMock()]  # モックfacets
        
        result = handle_urls_in_text(text, facets=facets)
        
        self.assertTrue(result)
        # facetsから抽出されたURLが優先されることを確認
        mock_open_url.assert_called_once_with("https://facet-url.com")
    
    @patch('utils.url_utils.wx.SingleChoiceDialog')
    def test_handle_urls_in_text_dialog_cancel(self, mock_dialog):
        """URL選択ダイアログでキャンセルされた場合のテスト"""
        # ダイアログのモック設定（キャンセル）
        mock_dlg = MagicMock()
        mock_dlg.ShowModal.return_value = 0  # wx.ID_CANCEL
        mock_dialog.return_value = mock_dlg
        
        mock_parent = MagicMock()
        text = "https://example.com と https://test.org"
        result = handle_urls_in_text(text, parent=mock_parent)
        
        self.assertFalse(result)
        mock_dlg.Destroy.assert_called()
    
    def test_url_pattern_edge_cases(self):
        """URL正規表現パターンのエッジケースのテスト"""
        # ドット付きドメイン
        text = "サブドメイン: https://sub.domain.example.com"
        urls = extract_urls(text)
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "https://sub.domain.example.com")
        
        # ポート番号付き
        text = "ローカル: http://localhost:8080/api"
        urls = extract_urls(text)
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "http://localhost:8080/api")
        
        # パーセントエンコーディング
        text = "エンコード: https://example.com/path%20with%20spaces"
        urls = extract_urls(text)
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "https://example.com/path%20with%20spaces")

if __name__ == '__main__':
    unittest.main()