#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
プロトコル定義モジュール（型インターフェース）
"""

from typing import Protocol, Optional, Dict, Any, List
from abc import abstractmethod


class ConfigManagerProtocol(Protocol):
    """設定管理クラスのプロトコル定義"""
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        ...
    
    def set_value(self, key: str, value: Any) -> bool:
        """設定値を保存"""
        ...
    
    def save_config(self) -> bool:
        """設定をファイルに保存"""
        ...
    
    def load_config(self) -> bool:
        """設定をファイルから読み込み"""
        ...


class AuthManagerProtocol(Protocol):
    """認証管理クラスのプロトコル定義"""
    
    @property
    def is_logged_in(self) -> bool:
        """ログイン状態を取得"""
        ...
    
    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """ログイン処理"""
        ...
    
    def login_with_session(self, session_string: str) -> Optional[Dict[str, Any]]:
        """セッション情報でログイン"""
        ...
    
    def logout(self) -> bool:
        """ログアウト処理"""
        ...
    
    def export_session_string(self) -> Optional[str]:
        """セッション情報のエクスポート"""
        ...


class ApiClientProtocol(Protocol):
    """APIクライアントのプロトコル定義"""
    
    def get_timeline(self, limit: int = 50) -> Optional[Dict[str, Any]]:
        """タイムライン取得"""
        ...
    
    def send_post(self, text: str, images: Optional[List[Any]] = None) -> Optional[Dict[str, Any]]:
        """投稿送信"""
        ...
    
    def upload_blob(self, file_data: bytes, mime_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """ファイルアップロード"""
        ...
    
    def like(self, uri: str, cid: str) -> Optional[Dict[str, Any]]:
        """いいね処理"""
        ...


class DataStoreProtocol(Protocol):
    """データストアのプロトコル定義"""
    
    def init_database(self) -> bool:
        """データベース初期化"""
        ...
    
    def save_encrypted_session(self, user_did: str, session_string: str) -> bool:
        """暗号化セッション保存"""
        ...
    
    def load_encrypted_session(self, user_did: str) -> Optional[str]:
        """暗号化セッション読み込み"""
        ...
    
    def delete_session(self, user_did: str) -> bool:
        """セッション削除"""
        ...


class EventPublisherProtocol(Protocol):
    """イベント発行者のプロトコル定義"""
    
    def publish_event(self, event_name: str, **kwargs: Any) -> None:
        """イベント発行"""
        ...
    
    def subscribe_event(self, event_name: str, callback: Any) -> None:
        """イベント購読"""
        ...


class CryptoProtocol(Protocol):
    """暗号化処理のプロトコル定義"""
    
    def encrypt_data(self, data: str) -> Optional[bytes]:
        """データ暗号化"""
        ...
    
    def decrypt_data(self, encrypted_data: bytes) -> Optional[str]:
        """データ復号化"""
        ...