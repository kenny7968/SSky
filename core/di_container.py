#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
依存性注入コンテナ（Phase 3）
"""

import logging
from typing import Dict, Any, Callable, Type, Optional, TypeVar, Union
import inspect
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DIContainer:
    """軽量依存性注入コンテナ
    
    Phase 3で追加された依存性注入をサポートするコンテナクラス。
    シングルトンとトランジェントインスタンスの管理をサポートし、
    テスト時の依存性差し替えを簡単にします。
    """
    
    def __init__(self):
        """初期化"""
        self._services: Dict[str, Any] = {}           # 登録されたサービス
        self._singletons: Dict[str, Any] = {}         # シングルトンインスタンス
        self._factories: Dict[str, Callable] = {}     # ファクトリ関数
        self._lifetimes: Dict[str, str] = {}          # ライフタイム設定
        
    def register_singleton(self, service_type: Type[T], implementation: Union[Type[T], T] = None) -> 'DIContainer':
        """シングルトンサービスを登録
        
        Args:
            service_type: サービスの型
            implementation: 実装クラスまたはインスタンス
            
        Returns:
            DIContainer: メソッドチェーン用
        """
        key = self._get_key(service_type)
        
        if implementation is None:
            implementation = service_type
            
        if inspect.isclass(implementation):
            self._services[key] = implementation
        else:
            # 既存のインスタンスの場合はそのまま保存
            self._singletons[key] = implementation
            
        self._lifetimes[key] = 'singleton'
        logger.debug(f"Registered singleton: {key}")
        return self
    
    def register_transient(self, service_type: Type[T], implementation: Type[T] = None) -> 'DIContainer':
        """トランジェントサービスを登録
        
        Args:
            service_type: サービスの型
            implementation: 実装クラス
            
        Returns:
            DIContainer: メソッドチェーン用
        """
        key = self._get_key(service_type)
        
        if implementation is None:
            implementation = service_type
            
        self._services[key] = implementation
        self._lifetimes[key] = 'transient'
        logger.debug(f"Registered transient: {key}")
        return self
    
    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> 'DIContainer':
        """ファクトリ関数を登録
        
        Args:
            service_type: サービスの型
            factory: インスタンスを作成するファクトリ関数
            
        Returns:
            DIContainer: メソッドチェーン用
        """
        key = self._get_key(service_type)
        self._factories[key] = factory
        self._lifetimes[key] = 'factory'
        logger.debug(f"Registered factory: {key}")
        return self
    
    def register_instance(self, service_type: Type[T], instance: T) -> 'DIContainer':
        """インスタンスを直接登録（シングルトンとして）
        
        Args:
            service_type: サービスの型
            instance: 登録するインスタンス
            
        Returns:
            DIContainer: メソッドチェーン用
        """
        key = self._get_key(service_type)
        self._singletons[key] = instance
        self._lifetimes[key] = 'singleton'
        logger.debug(f"Registered instance: {key}")
        return self
    
    def resolve(self, service_type: Type[T]) -> T:
        """サービスを解決
        
        Args:
            service_type: 解決するサービスの型
            
        Returns:
            サービスのインスタンス
            
        Raises:
            ValueError: サービスが登録されていない場合
        """
        key = self._get_key(service_type)
        
        # 既存のシングルトンインスタンスがあるかチェック
        if key in self._singletons:
            return self._singletons[key]
        
        # ファクトリが登録されている場合
        if key in self._factories:
            instance = self._factories[key]()
            if self._lifetimes.get(key) == 'singleton':
                self._singletons[key] = instance
            return instance
        
        # サービスが登録されているかチェック
        if key not in self._services:
            raise ValueError(f"Service not registered: {service_type}")
        
        service_class = self._services[key]
        
        # コンストラクタの引数を解決
        instance = self._create_instance(service_class)
        
        # シングルトンの場合は保存
        if self._lifetimes.get(key) == 'singleton':
            self._singletons[key] = instance
            
        return instance
    
    def resolve_optional(self, service_type: Type[T]) -> Optional[T]:
        """サービスを解決（見つからない場合はNoneを返す）
        
        Args:
            service_type: 解決するサービスの型
            
        Returns:
            サービスのインスタンス、または None
        """
        try:
            return self.resolve(service_type)
        except ValueError:
            return None
    
    def clear(self):
        """全ての登録を削除"""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()
        self._lifetimes.clear()
        logger.debug("Container cleared")
    
    def create_child(self) -> 'DIContainer':
        """子コンテナを作成（親の設定を継承）
        
        Returns:
            DIContainer: 新しい子コンテナ
        """
        child = DIContainer()
        child._services = self._services.copy()
        child._factories = self._factories.copy()
        child._lifetimes = self._lifetimes.copy()
        # シングルトンは継承しない（子コンテナで独立）
        return child
    
    def _get_key(self, service_type: Type) -> str:
        """サービスタイプからキーを生成"""
        if hasattr(service_type, '__name__'):
            return service_type.__name__
        else:
            return str(service_type)
    
    def _create_instance(self, service_class: Type[T]) -> T:
        """インスタンスを作成（依存性を自動解決）"""
        try:
            # コンストラクタのシグネチャを取得
            sig = inspect.signature(service_class.__init__)
            params = {}
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                    
                # 型ヒントがある場合は依存性を解決
                if param.annotation != inspect.Parameter.empty:
                    dependency = self.resolve_optional(param.annotation)
                    if dependency is not None:
                        params[param_name] = dependency
                    elif param.default == inspect.Parameter.empty:
                        # 必須パラメータが解決できない場合はログに記録
                        logger.warning(f"Cannot resolve required dependency: {param.annotation} for {service_class}")
            
            return service_class(**params)
            
        except Exception as e:
            logger.error(f"Failed to create instance of {service_class}: {str(e)}")
            # フォールバック: 引数なしで作成を試行
            return service_class()


# グローバルコンテナインスタンス
_default_container = DIContainer()


def get_container() -> DIContainer:
    """デフォルトコンテナを取得"""
    return _default_container


def configure_default_services():
    """デフォルトサービスを設定
    
    SSkyアプリケーションの標準的な依存関係を設定します。
    """
    from core.data_store import DataStore
    from core.auth.credential_manager import AuthCredentialManager
    from core.client.api_client import BlueskyApiClient
    from core.client.facade import BlueskyClient
    
    container = get_container()
    
    # データストア（シングルトン）
    container.register_singleton(DataStore)
    
    # 認証情報管理（トランジェント - テストでの状態分離のため）
    container.register_transient(AuthCredentialManager)
    
    # APIクライアント（トランジェント）
    container.register_transient(BlueskyApiClient)
    
    # メインクライアント（トランジェント）
    container.register_transient(BlueskyClient)
    
    logger.info("Default services configured")


def configure_test_services():
    """テスト用サービスを設定
    
    テスト環境での依存関係を設定します。
    """
    from core.data_store import DataStore
    from core.auth.credential_manager import AuthCredentialManager
    
    container = get_container()
    container.clear()
    
    # テスト用データストア（メモリ内）
    container.register_factory(DataStore, DataStore.create_in_memory)
    
    # テスト用認証情報管理
    container.register_transient(AuthCredentialManager)
    
    logger.info("Test services configured")


# 便利なデコレータ
def inject(container: DIContainer = None):
    """依存性注入デコレータ
    
    Args:
        container: 使用するコンテナ（未指定時はデフォルト）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if container is None:
                used_container = get_container()
            else:
                used_container = container
            
            # 関数の引数に依存性を注入
            sig = inspect.signature(func)
            for param_name, param in sig.parameters.items():
                if param_name not in kwargs and param.annotation != inspect.Parameter.empty:
                    dependency = used_container.resolve_optional(param.annotation)
                    if dependency is not None:
                        kwargs[param_name] = dependency
            
            return func(*args, **kwargs)
        return wrapper
    return decorator