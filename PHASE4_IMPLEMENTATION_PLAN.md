# SSky Phase 4 実装計画
## アーキテクチャ改善と高品質テスト戦略

### 概要

Phase 3完了後、SSkyプロジェクトは以下の状況にあります：

- **Phase 1-3実績**: unittest 100%成功率（107/107テスト）達成済み
- **pytest環境**: 完全構築済み、276テスト実装済み
- **現在の課題**: pytest統合・E2Eテストで49エラー・43失敗発生中
- **次期目標**: アーキテクチャ改善によりテスト品質とコードの保守性向上

### Phase 4 の目標

1. **統合テストの安定化**: pytest環境での49エラー・43失敗の解決
2. **依存性注入の導入**: テスト容易性とコードの疎結合化
3. **MVPパターン部分導入**: GUI依存性の削減と単体テスト容易性向上
4. **E2Eテスト実装**: 実際のユーザーシナリオテスト
5. **高度なカバレッジ分析**: ブランチカバレッジとパフォーマンス回帰テスト

## 実装計画

### 1. 統合テスト修正 (Week 1-2)

#### 1.1 エラー分析と分類
現在の49エラー・43失敗の根本原因分析：

**主要エラーパターン**:
- モジュールインポートエラー
- fixture設定の不整合
- 非同期処理の同期問題
- シングルトンパターンのテスト分離問題

**修正アプローチ**:
```python
# エラー例: ModuleNotFoundError
# 原因: 相対インポートパスの問題
# 解決策: conftest.pyでのパス設定強化

# tests/conftest.py の改善
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture(autouse=True)
def reset_singletons():
    """テスト間でシングルトンインスタンスをリセット"""
    from core.auth.credential_manager import AuthCredentialManager
    from config.settings_manager import SettingsManager
    
    # シングルトンインスタンスのクリア
    AuthCredentialManager._instances.clear()
    SettingsManager._instance = None
    yield
```

#### 1.2 統合テスト安定化戦略

**認証フロー統合テスト**:
```python
# tests/integration/test_auth_flow_stable.py
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os

class TestStableAuthFlow:
    @pytest.fixture
    def temp_db(self):
        """一時データベースでテスト分離"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            temp_db_path = f.name
        yield temp_db_path
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
    
    @pytest.fixture
    def mock_client(self):
        """安定したAPIクライアントモック"""
        with patch('core.client.api_client.Client') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            yield mock_instance
    
    def test_complete_auth_flow_with_isolation(self, temp_db, mock_client):
        """完全に分離された認証フローテスト"""
        # 実装...
```

### 2. 依存性注入パターン導入 (Week 2-3)

#### 2.1 DIコンテナ実装

```python
# core/di_container.py - 新規作成
from typing import Dict, Type, Any, Optional
import threading

class DIContainer:
    """簡易依存性注入コンテナ"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._services = {}
                    cls._instance._singletons = {}
        return cls._instance
    
    def register_singleton(self, interface: Type, implementation: Type):
        """シングルトンサービスの登録"""
        self._services[interface] = (implementation, True)
    
    def register_transient(self, interface: Type, implementation: Type):
        """トランジェントサービスの登録"""
        self._services[interface] = (implementation, False)
    
    def resolve(self, interface: Type) -> Any:
        """サービスの解決"""
        if interface not in self._services:
            raise ValueError(f"Service {interface} not registered")
        
        implementation, is_singleton = self._services[interface]
        
        if is_singleton:
            if interface not in self._singletons:
                self._singletons[interface] = implementation()
            return self._singletons[interface]
        else:
            return implementation()
    
    def clear_singletons(self):
        """テスト用: シングルトンインスタンスクリア"""
        self._singletons.clear()
```

#### 2.2 コアクラスのDI対応リファクタリング

```python
# core/client/facade.py の改善
from core.di_container import DIContainer
from abc import ABC, abstractmethod

class IApiClient(ABC):
    """API クライアントのインターフェース"""
    @abstractmethod
    def get_timeline(self, limit: int = 50): pass
    
    @abstractmethod
    def send_post(self, text: str, images=None): pass

class ICredentialManager(ABC):
    """認証情報管理のインターフェース"""
    @abstractmethod
    def save_credentials(self, username: str, password: str): pass
    
    @abstractmethod
    def load_credentials(self): pass

class BlueskyClientDI:
    """依存性注入対応版 BlueskyClient"""
    
    def __init__(self, container: DIContainer = None):
        self.container = container or DIContainer()
        self._api_client = None
        self._credential_manager = None
    
    @property
    def api_client(self) -> IApiClient:
        if self._api_client is None:
            self._api_client = self.container.resolve(IApiClient)
        return self._api_client
    
    @property
    def credential_manager(self) -> ICredentialManager:
        if self._credential_manager is None:
            self._credential_manager = self.container.resolve(ICredentialManager)
        return self._credential_manager
    
    def login(self, username: str, password: str) -> bool:
        """依存性注入されたサービスを使用したログイン"""
        # 実装...
```

### 3. MVPパターン部分導入 (Week 3-4)

#### 3.1 タイムラインプレゼンター

```python
# gui/presenters/timeline_presenter.py - 新規作成
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from core.client.facade import BlueskyClientDI

class ITimelineView(ABC):
    """タイムラインビューのインターフェース"""
    @abstractmethod
    def display_posts(self, posts: List[Dict[str, Any]]): pass
    
    @abstractmethod
    def show_loading(self, is_loading: bool): pass
    
    @abstractmethod
    def show_error(self, message: str): pass

class TimelinePresenter:
    """タイムラインのプレゼンター（ビジネスロジック）"""
    
    def __init__(self, view: ITimelineView, client: BlueskyClientDI):
        self.view = view
        self.client = client
        self._current_posts = []
    
    async def load_timeline(self, limit: int = 50):
        """タイムライン読み込み"""
        try:
            self.view.show_loading(True)
            posts = await self.client.api_client.get_timeline(limit)
            formatted_posts = self._format_posts(posts)
            self._current_posts = formatted_posts
            self.view.display_posts(formatted_posts)
        except Exception as e:
            self.view.show_error(f"タイムライン読み込みエラー: {str(e)}")
        finally:
            self.view.show_loading(False)
    
    def _format_posts(self, raw_posts: List[Dict]) -> List[Dict[str, Any]]:
        """投稿データの整形（GUI非依存）"""
        formatted = []
        for post in raw_posts:
            formatted.append({
                'text': post.get('record', {}).get('text', ''),
                'author': post.get('author', {}).get('display_name', ''),
                'created_at': post.get('record', {}).get('created_at', ''),
                'formatted_time': self._format_time(post.get('record', {}).get('created_at')),
                'reply_count': post.get('reply_count', 0),
                'repost_count': post.get('repost_count', 0),
                'like_count': post.get('like_count', 0)
            })
        return formatted
    
    def _format_time(self, timestamp: str) -> str:
        """時間フォーマット（ユーティリティ使用）"""
        from utils.time_format import format_relative_time
        return format_relative_time(timestamp)
```

#### 3.2 MVPパターン用テスト

```python
# tests/unit/gui/test_timeline_presenter.py - 新規作成
import pytest
from unittest.mock import Mock, AsyncMock, patch
from gui.presenters.timeline_presenter import TimelinePresenter, ITimelineView

class MockTimelineView:
    """テスト用ビューモック"""
    def __init__(self):
        self.displayed_posts = []
        self.loading_states = []
        self.error_messages = []
    
    def display_posts(self, posts):
        self.displayed_posts = posts
    
    def show_loading(self, is_loading):
        self.loading_states.append(is_loading)
    
    def show_error(self, message):
        self.error_messages.append(message)

class TestTimelinePresenter:
    @pytest.fixture
    def mock_view(self):
        return MockTimelineView()
    
    @pytest.fixture
    def mock_client(self):
        client = Mock()
        client.api_client = Mock()
        return client
    
    @pytest.fixture
    def presenter(self, mock_view, mock_client):
        return TimelinePresenter(mock_view, mock_client)
    
    @pytest.mark.asyncio
    async def test_load_timeline_success(self, presenter, mock_view, mock_client):
        """タイムライン読み込み成功のテスト"""
        # モックデータ設定
        mock_posts = [
            {
                'record': {'text': 'Test post', 'created_at': '2024-01-01T00:00:00Z'},
                'author': {'display_name': 'Test User'},
                'reply_count': 1, 'repost_count': 2, 'like_count': 3
            }
        ]
        mock_client.api_client.get_timeline = AsyncMock(return_value=mock_posts)
        
        # テスト実行
        await presenter.load_timeline()
        
        # 検証
        assert len(mock_view.displayed_posts) == 1
        assert mock_view.displayed_posts[0]['text'] == 'Test post'
        assert mock_view.displayed_posts[0]['author'] == 'Test User'
        assert True in mock_view.loading_states  # ローディング開始
        assert False in mock_view.loading_states  # ローディング終了
        assert len(mock_view.error_messages) == 0
    
    @pytest.mark.asyncio
    async def test_load_timeline_error(self, presenter, mock_view, mock_client):
        """タイムライン読み込みエラーのテスト"""
        # エラーを発生させる
        mock_client.api_client.get_timeline = AsyncMock(side_effect=Exception("API Error"))
        
        # テスト実行
        await presenter.load_timeline()
        
        # 検証
        assert len(mock_view.displayed_posts) == 0
        assert len(mock_view.error_messages) == 1
        assert "API Error" in mock_view.error_messages[0]
        assert False in mock_view.loading_states  # エラー後もローディング終了
    
    def test_format_posts_data_transformation(self, presenter):
        """投稿データ整形のテスト（同期）"""
        raw_posts = [
            {
                'record': {'text': 'Hello World', 'created_at': '2024-01-01T00:00:00Z'},
                'author': {'display_name': 'John Doe'},
                'reply_count': 5, 'repost_count': 10, 'like_count': 15
            }
        ]
        
        with patch('utils.time_format.format_relative_time', return_value='1日前'):
            formatted = presenter._format_posts(raw_posts)
        
        assert len(formatted) == 1
        post = formatted[0]
        assert post['text'] == 'Hello World'
        assert post['author'] == 'John Doe'
        assert post['formatted_time'] == '1日前'
        assert post['reply_count'] == 5
        assert post['repost_count'] == 10
        assert post['like_count'] == 15
```

### 4. E2Eテスト実装 (Week 4-5)

#### 4.1 ユーザーシナリオE2Eテスト

```python
# tests/e2e/test_user_scenarios.py - 新規作成
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os
from core.di_container import DIContainer

class TestUserScenarios:
    """実際のユーザー使用シナリオのE2Eテスト"""
    
    @pytest.fixture
    def integration_environment(self):
        """E2Eテスト用統合環境"""
        # 一時ディレクトリとDB
        temp_dir = tempfile.mkdtemp()
        temp_db = os.path.join(temp_dir, 'test_ssky.db')
        
        # DIコンテナ初期化
        container = DIContainer()
        container.clear_singletons()
        
        yield {
            'temp_dir': temp_dir,
            'temp_db': temp_db,
            'container': container
        }
        
        # クリーンアップ
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        container.clear_singletons()
    
    @pytest.mark.e2e
    def test_complete_user_session_scenario(self, integration_environment):
        """完全なユーザーセッションのE2Eテスト"""
        env = integration_environment
        
        # シナリオ: 新規ユーザーのアプリ使用
        with patch('core.client.api_client.Client') as mock_api:
            # Step 1: アプリ起動
            mock_api.return_value.login.return_value = True
            
            # Step 2: 初回ログイン
            from core.client.facade import BlueskyClientDI
            client = BlueskyClientDI(env['container'])
            
            login_success = client.login("test@example.com", "password")
            assert login_success == True
            
            # Step 3: タイムライン読み込み
            mock_api.return_value.get_timeline.return_value = [
                {'record': {'text': 'Hello World'}, 'author': {'display_name': 'Test'}}
            ]
            
            timeline = client.get_timeline()
            assert len(timeline) == 1
            
            # Step 4: 投稿作成
            mock_api.return_value.send_text.return_value = {'uri': 'at://test'}
            
            post_result = client.create_post("My first post!")
            assert post_result['uri'] == 'at://test'
            
            # Step 5: ログアウト
            logout_success = client.logout()
            assert logout_success == True
    
    @pytest.mark.e2e
    def test_error_recovery_scenario(self, integration_environment):
        """エラー回復シナリオのE2Eテスト"""
        env = integration_environment
        
        with patch('core.client.api_client.Client') as mock_api:
            # ネットワークエラーシミュレーション
            from requests.exceptions import ConnectionError
            mock_api.return_value.get_timeline.side_effect = ConnectionError("Network Error")
            
            from core.client.facade import BlueskyClientDI
            client = BlueskyClientDI(env['container'])
            
            # エラー発生時の挙動テスト
            with pytest.raises(ConnectionError):
                client.get_timeline()
            
            # 回復後の正常動作テスト
            mock_api.return_value.get_timeline.side_effect = None
            mock_api.return_value.get_timeline.return_value = []
            
            timeline = client.get_timeline()
            assert timeline == []
    
    @pytest.mark.e2e
    @pytest.mark.performance
    def test_performance_scenario(self, integration_environment):
        """パフォーマンスシナリオのE2Eテスト"""
        import time
        
        env = integration_environment
        
        with patch('core.client.api_client.Client') as mock_api:
            # 大量データシミュレーション
            large_timeline = [
                {'record': {'text': f'Post {i}'}, 'author': {'display_name': f'User{i}'}}
                for i in range(1000)
            ]
            mock_api.return_value.get_timeline.return_value = large_timeline
            
            from core.client.facade import BlueskyClientDI
            client = BlueskyClientDI(env['container'])
            
            # パフォーマンス測定
            start_time = time.time()
            timeline = client.get_timeline()
            end_time = time.time()
            
            # 性能要件チェック（1000件を1秒以内で処理）
            processing_time = end_time - start_time
            assert processing_time < 1.0, f"Processing took {processing_time:.2f}s, expected < 1.0s"
            assert len(timeline) == 1000
```

#### 4.2 GUI E2Eテスト（MVPパターン活用）

```python
# tests/e2e/test_gui_scenarios.py - 新規作成
import pytest
from unittest.mock import Mock, AsyncMock, patch
from gui.presenters.timeline_presenter import TimelinePresenter

class TestGUIScenarios:
    """GUI操作シナリオのE2Eテスト"""
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_timeline_interaction_scenario(self):
        """タイムライン操作の完全シナリオ"""
        # モックビューとクライアント
        mock_view = Mock()
        mock_client = Mock()
        mock_client.api_client.get_timeline = AsyncMock()
        
        presenter = TimelinePresenter(mock_view, mock_client)
        
        # シナリオ1: 初回タイムライン読み込み
        mock_client.api_client.get_timeline.return_value = [
            {
                'record': {'text': 'First post', 'created_at': '2024-01-01T00:00:00Z'},
                'author': {'display_name': 'Alice'},
                'reply_count': 1, 'repost_count': 2, 'like_count': 3
            }
        ]
        
        await presenter.load_timeline(limit=50)
        
        # 検証: ビューが正しく更新される
        mock_view.show_loading.assert_any_call(True)
        mock_view.show_loading.assert_any_call(False)
        mock_view.display_posts.assert_called_once()
        
        displayed_posts = mock_view.display_posts.call_args[0][0]
        assert len(displayed_posts) == 1
        assert displayed_posts[0]['text'] == 'First post'
        assert displayed_posts[0]['author'] == 'Alice'
        
        # シナリオ2: リフレッシュ操作
        mock_view.reset_mock()
        mock_client.api_client.get_timeline.return_value = [
            {
                'record': {'text': 'New post', 'created_at': '2024-01-02T00:00:00Z'},
                'author': {'display_name': 'Bob'},
                'reply_count': 0, 'repost_count': 1, 'like_count': 5
            }
        ]
        
        await presenter.load_timeline(limit=50)
        
        # 検証: 新しい投稿が表示される
        displayed_posts = mock_view.display_posts.call_args[0][0]
        assert len(displayed_posts) == 1
        assert displayed_posts[0]['text'] == 'New post'
        assert displayed_posts[0]['author'] == 'Bob'
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_error_handling_gui_scenario(self):
        """GUIでのエラーハンドリングシナリオ"""
        mock_view = Mock()
        mock_client = Mock()
        
        presenter = TimelinePresenter(mock_view, mock_client)
        
        # エラーシナリオ: ネットワーク障害
        from requests.exceptions import ConnectionError
        mock_client.api_client.get_timeline = AsyncMock(
            side_effect=ConnectionError("Network unreachable")
        )
        
        await presenter.load_timeline()
        
        # 検証: エラーメッセージがユーザーに表示される
        mock_view.show_error.assert_called_once()
        error_message = mock_view.show_error.call_args[0][0]
        assert "Network unreachable" in error_message
        assert "タイムライン読み込みエラー" in error_message
        
        # ローディング状態が適切に終了される
        mock_view.show_loading.assert_any_call(False)
```

### 5. 高度なカバレッジ分析 (Week 5-6)

#### 5.1 ブランチカバレッジとパフォーマンス回帰テスト

```python
# scripts/advanced_coverage_analysis.py - 新規作成
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Any

class AdvancedCoverageAnalyzer:
    """高度なカバレッジ分析ツール"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {}
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """包括的カバレッジ分析実行"""
        print("🔍 高度なカバレッジ分析を開始...")
        
        # 1. ブランチカバレッジ分析
        branch_coverage = self._analyze_branch_coverage()
        
        # 2. パフォーマンス回帰テスト
        performance_results = self._run_performance_regression_tests()
        
        # 3. コードパス分析
        code_path_analysis = self._analyze_code_paths()
        
        # 4. カバレッジホットスポット特定
        hotspots = self._identify_coverage_hotspots()
        
        self.results = {
            'branch_coverage': branch_coverage,
            'performance': performance_results,
            'code_paths': code_path_analysis,
            'hotspots': hotspots,
            'timestamp': time.time()
        }
        
        return self.results
    
    def _analyze_branch_coverage(self) -> Dict[str, Any]:
        """ブランチカバレッジ分析"""
        print("📊 ブランチカバレッジ分析中...")
        
        # pytest-covでブランチカバレッジ実行
        cmd = [
            'pytest', '--cov=core', '--cov=utils', '--cov=config',
            '--cov-branch', '--cov-report=json:coverage_branch.json',
            'tests/unit/', '-q'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        
        if result.returncode == 0:
            with open(self.project_root / 'coverage_branch.json', 'r', encoding='utf-8') as f:
                coverage_data = json.load(f)
            
            return self._process_branch_coverage(coverage_data)
        else:
            print(f"❌ ブランチカバレッジ分析エラー: {result.stderr}")
            return {'error': result.stderr}
    
    def _process_branch_coverage(self, coverage_data: Dict) -> Dict[str, Any]:
        """ブランチカバレッジデータ処理"""
        files_analysis = {}
        total_branches = 0
        covered_branches = 0
        
        for filename, file_data in coverage_data['files'].items():
            if 'summary' in file_data:
                file_branches = file_data['summary'].get('num_branches', 0)
                file_covered = file_data['summary'].get('covered_branches', 0)
                
                total_branches += file_branches
                covered_branches += file_covered
                
                files_analysis[filename] = {
                    'total_branches': file_branches,
                    'covered_branches': file_covered,
                    'branch_coverage': (file_covered / file_branches * 100) if file_branches > 0 else 100
                }
        
        overall_branch_coverage = (covered_branches / total_branches * 100) if total_branches > 0 else 100
        
        return {
            'overall_branch_coverage': overall_branch_coverage,
            'total_branches': total_branches,
            'covered_branches': covered_branches,
            'files': files_analysis
        }
    
    def _run_performance_regression_tests(self) -> Dict[str, Any]:
        """パフォーマンス回帰テスト実行"""
        print("⚡ パフォーマンス回帰テスト実行中...")
        
        # パフォーマンステスト実行
        cmd = [
            'pytest', 'tests/performance/', '-v',
            '--benchmark-only', '--benchmark-json=benchmark_results.json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        
        if result.returncode == 0 and Path(self.project_root / 'benchmark_results.json').exists():
            with open(self.project_root / 'benchmark_results.json', 'r', encoding='utf-8') as f:
                benchmark_data = json.load(f)
            return self._process_benchmark_results(benchmark_data)
        else:
            # Fallback: 手動でパフォーマンステスト実行
            return self._run_manual_performance_tests()
    
    def _run_manual_performance_tests(self) -> Dict[str, Any]:
        """手動パフォーマンステスト"""
        performance_results = {}
        
        # タイムライン処理性能テスト
        start_time = time.time()
        
        from tests.factories.post_factory import PostFactory
        large_timeline = PostFactory.build_batch(1000)
        
        processing_time = time.time() - start_time
        
        performance_results['timeline_processing'] = {
            'data_size': 1000,
            'processing_time': processing_time,
            'items_per_second': 1000 / processing_time if processing_time > 0 else float('inf')
        }
        
        return performance_results
    
    def _analyze_code_paths(self) -> Dict[str, Any]:
        """コードパス分析"""
        print("🛣️ コードパス分析中...")
        
        # 重要な実行パスの特定
        critical_paths = [
            'core.client.facade.BlueskyClient.login',
            'core.client.facade.BlueskyClient.get_timeline',
            'core.client.facade.BlueskyClient.create_post',
            'core.auth.credential_manager.AuthCredentialManager.save_credentials',
            'core.data_store.DataStore.save_session'
        ]
        
        path_analysis = {}
        
        for path in critical_paths:
            # パスカバレッジチェック（簡易実装）
            cmd = [
                'pytest', '--cov=' + path.split('.')[0], '--cov-report=term-missing',
                'tests/unit/', '-q'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            path_analysis[path] = {
                'covered': 'TOTAL' in result.stdout,
                'details': result.stdout
            }
        
        return path_analysis
    
    def _identify_coverage_hotspots(self) -> List[Dict[str, Any]]:
        """カバレッジホットスポット特定"""
        print("🎯 カバレッジホットスポット特定中...")
        
        hotspots = []
        
        # 低カバレッジファイルの特定
        if 'branch_coverage' in self.results and 'files' in self.results['branch_coverage']:
            for filename, analysis in self.results['branch_coverage']['files'].items():
                if analysis['branch_coverage'] < 80:  # 80%未満を要改善とする
                    hotspots.append({
                        'file': filename,
                        'coverage': analysis['branch_coverage'],
                        'priority': 'high' if analysis['branch_coverage'] < 60 else 'medium',
                        'uncovered_branches': analysis['total_branches'] - analysis['covered_branches']
                    })
        
        # 優先度順にソート
        hotspots.sort(key=lambda x: x['coverage'])
        
        return hotspots
    
    def generate_report(self) -> str:
        """分析レポート生成"""
        report = []
        report.append("# SSky 高度カバレッジ分析レポート")
        report.append(f"生成時刻: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        if 'branch_coverage' in self.results:
            bc = self.results['branch_coverage']
            report.append("## ブランチカバレッジ分析")
            report.append(f"- **全体ブランチカバレッジ**: {bc['overall_branch_coverage']:.1f}%")
            report.append(f"- **総ブランチ数**: {bc['total_branches']}")
            report.append(f"- **カバー済ブランチ数**: {bc['covered_branches']}")
            report.append("")
        
        if 'performance' in self.results:
            perf = self.results['performance']
            report.append("## パフォーマンス分析")
            for test_name, test_result in perf.items():
                report.append(f"- **{test_name}**: {test_result}")
            report.append("")
        
        if 'hotspots' in self.results and self.results['hotspots']:
            report.append("## 改善推奨ファイル")
            for hotspot in self.results['hotspots'][:5]:  # 上位5件
                report.append(f"- **{hotspot['file']}**: {hotspot['coverage']:.1f}% "
                            f"(優先度: {hotspot['priority']})")
            report.append("")
        
        return "\n".join(report)
    
    def save_report(self, filename: str = "advanced_coverage_report.md"):
        """レポート保存"""
        report_content = self.generate_report()
        report_path = self.project_root / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 レポートを保存しました: {report_path}")
        return report_path

if __name__ == "__main__":
    analyzer = AdvancedCoverageAnalyzer(".")
    results = analyzer.run_comprehensive_analysis()
    analyzer.save_report()
    
    print("✅ 高度なカバレッジ分析完了")
```

## Phase 4 実装スケジュール

### Week 1-2: 統合テスト修正
- [ ] pytest環境でのエラー原因分析
- [ ] conftest.py改善とfixture再設計
- [ ] 統合テストの段階的修正
- [ ] エラー数50%削減目標

### Week 3-4: アーキテクチャ改善
- [ ] DIコンテナ実装
- [ ] コアクラスのDI対応リファクタリング
- [ ] MVPパターン部分導入
- [ ] プレゼンター層の実装とテスト

### Week 4-5: E2Eテスト
- [ ] ユーザーシナリオE2Eテスト実装
- [ ] GUI E2Eテスト（MVPパターン活用）
- [ ] パフォーマンスE2Eテスト
- [ ] エラー回復シナリオテスト

### Week 5-6: 高度分析とレポート
- [ ] ブランチカバレッジ分析実装
- [ ] パフォーマンス回帰テストシステム
- [ ] カバレッジホットスポット分析
- [ ] Phase 4完了レポート作成

## 成功指標

### テスト品質指標
- **pytest統合テスト成功率**: 現在66% → 目標90%+
- **ブランチカバレッジ**: 目標85%+
- **E2Eテスト実装**: 主要ユーザーシナリオ10+件

### アーキテクチャ指標
- **依存性注入適用**: コアクラス5+箇所
- **MVP分離度**: GUI依存コード50%削減
- **テスト実行時間**: 現在18.59秒 → 目標15秒以下

### 保守性指標
- **コードの疎結合化**: 依存関係グラフの改善
- **テストの再利用性**: ファクトリ・フィクスチャ活用度
- **エラーハンドリング統一**: 統一エラーハンドリング100%適用

---

この計画により、SSkyプロジェクトは Phase 1-3の成果を基盤に、さらなる品質向上とアーキテクチャ改善を実現します。特に、実際の開発・保守フェーズで重要となるテスト容易性とコードの拡張性を大幅に向上させることができます。