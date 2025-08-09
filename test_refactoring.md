# SSkyプロジェクト テスト戦略再設計計画

## 概要

SSkyは画面読み上げソフトウェア対応のBlueskyクライアントで、wxPythonベースのGUIアプリケーションです。現在205個のテストケースが実装されていますが、66個のエラーと11個の失敗が発生しており、テスト戦略の見直しが必要です。

## 現状分析

### プロジェクト構造
- **エントリーポイント**: `SSky.py`
- **コア層** (`core/`): ビジネスロジックとAPI通信
- **GUI層** (`gui/`): ユーザーインターフェース
- **設定管理** (`config/`): アプリケーション設定
- **ユーティリティ** (`utils/`): 共通機能

### 現状の問題点

#### 1. テスト実行環境の問題
- **高エラー率**: 66/205 (32.2%) のエラー率
- **インポートエラー**: 設定ファイルやモジュールのインポートに失敗
- **依存関係の問題**: wxPythonやWindows固有の機能（DPAPI）への依存

#### 2. テストの品質問題
- **モック設定の不整合**: エラーメッセージの期待値と実際値の相違
- **非同期処理の不適切なテスト**: スレッド処理のテストで適切な同期が取れていない
- **正規表現パターンの不備**: URL検出ロジックのテストで期待値が不正確

#### 3. アーキテクチャ上の課題
- **GUI依存性**: wxPython MessageBoxなどのUI要素への強い結合
- **シングルトンパターン**: テスト間での状態分離が困難
- **プラットフォーム依存**: Windows DPAPIなど、テスト環境に依存する機能

## テスト戦略提案

### 1. テストピラミッドの適用

```
     [E2E Tests]         <- 少数の重要なユーザーシナリオのみ
    [Integration Tests]   <- コンポーネント間の連携テスト
 [Unit Tests (多数)]      <- 個別クラス・関数の徹底テスト
```

### 2. レイヤー別テスト戦略

#### Unit Tests (単体テスト) - 優先度：高

**対象コンポーネント:**
- `core/client/api_client.py`: APIクライアント（atproto通信をモック）
- `core/auth/credential_manager.py`: 認証管理（暗号化処理をモック）  
- `core/data_store.py`: データ永続化（一時DBでテスト）
- `utils/`: 各種ユーティリティ関数
- `config/`: 設定管理（ファイルI/Oをモック）

**改善例:**
```python
# 現在の問題例（期待値の不一致）
mock_msgbox.assert_called_once_with(
    "この操作にはログインが必要です", "エラー", unittest.mock.ANY
)
# 実際: MessageBox('削除に失敗しました: この操作にはログインが必要です', '警告', 260)

# 改善後の提案
def test_error_message_consistency(self):
    """エラーメッセージの一貫性確保"""
    with patch('wx.MessageBox') as mock_msgbox:
        # 実際のエラーハンドラーの動作に合わせたテスト
        expected_title = "警告"  # 実装に合わせて修正
        expected_style = 260     # wx.OK | wx.ICON_WARNING
        mock_msgbox.assert_called_with(
            ANY, expected_title, expected_style, ANY
        )
```

#### Integration Tests (統合テスト) - 優先度：中

**対象シナリオ:**
- 認証フロー: `credential_manager` + `data_store` + `auth_manager`
- 投稿フロー: `api_client` + `post_handlers` + `error_handler`
- 設定変更: `settings_manager` + Observer通知

**実装例:**
```python
class TestAuthIntegration(unittest.TestCase):
    def test_complete_login_flow(self):
        """完全なログインフローのテスト"""
        with patch('core.client.api_client.AtprotoClient'), \
             patch('utils.crypto.encrypt_data') as mock_encrypt, \
             tempfile.NamedTemporaryFile() as temp_db:
            
            # 実際のコンポーネントを使用（外部依存のみモック）
            data_store = DataStore(temp_db.name)
            credential_manager = AuthCredentialManager()
            client = BlueskyClient()
            
            # 統合テストのシナリオ実行
            success = client.login("test_user", "test_password")
            
            # 統合的な検証
            self.assertTrue(success)
            self.assertTrue(client.is_logged_in)
            mock_encrypt.assert_called()
```

#### GUI Tests - 優先度：低（リファクタリング推奨）

**現状の課題:**
- wxPython UI要素への直接依存
- イベント処理の複雑性
- 画面読み上げソフトウェアとの相互作用

**推奨アプローチ:**
```python
# MVPパターンへのリファクタリングを推奨
class TestTimelinePresenter(unittest.TestCase):
    def test_timeline_data_formatting(self):
        """ビジネスロジックとUI表示の分離テスト"""
        # UIから独立したプレゼンターのテスト
        presenter = TimelinePresenter()
        mock_view = MagicMock()
        
        timeline_data = [{"text": "test post", "created_at": "2024-01-01"}]
        presenter.update_timeline(mock_view, timeline_data)
        
        # UIの具体的な実装に依存しないテスト
        mock_view.display_posts.assert_called_once()
```

### 3. テストフレームワーク選定

#### メインフレームワーク: pytest + pytest-asyncio

```python
# 現在のunittestから移行推奨
import pytest
from unittest.mock import patch, MagicMock

class TestBlueskyApiClient:
    @pytest.fixture
    def api_client(self):
        with patch('core.client.api_client.AtprotoClient'):
            return BlueskyApiClient()
    
    @pytest.mark.asyncio
    async def test_get_timeline_async(self, api_client):
        """非同期処理の適切なテスト"""
        result = await api_client.get_timeline_async(limit=10)
        assert result is not None
```

#### 追加ツール:
- **pytest-mock**: モックの簡潔な記述
- **pytest-cov**: カバレッジレポート
- **pytest-xdist**: 並列テスト実行
- **factory_boy**: テストデータのファクトリ

### 4. 新しいディレクトリ構造

```
tests/
├── conftest.py              # pytest設定とフィクスチャ
├── factories/               # テストデータファクトリ
│   ├── __init__.py
│   ├── user_factory.py
│   └── post_factory.py
├── unit/                    # 単体テスト
│   ├── core/
│   │   ├── test_api_client.py
│   │   ├── test_auth_manager.py
│   │   ├── test_data_store.py
│   │   └── test_error_handler.py
│   ├── utils/
│   │   ├── test_auth_decorators.py
│   │   ├── test_crypto.py
│   │   └── test_time_format.py
│   └── config/
│       └── test_settings_manager.py
├── integration/             # 統合テスト
│   ├── test_auth_flow.py
│   ├── test_post_flow.py
│   └── test_settings_flow.py
├── e2e/                     # エンドツーエンドテスト
│   ├── test_login_scenarios.py
│   └── test_timeline_scenarios.py
└── fixtures/                # テストデータ
    ├── sample_posts.json
    └── sample_users.json
```

## コアモジュール分析

### 重要なコンポーネントとテスト観点

#### BlueskyApiClient (`core/client/api_client.py`)
- **役割**: atprotoライブラリのダイレクトラッパー
- **テストしやすい部分**: 各API操作メソッド、エラーハンドリングロジック
- **テストが困難な部分**: 実際のBluesky APIとの通信
- **モック対象**: `atproto.Client`

#### AuthCredentialManager (`core/auth/credential_manager.py`)
- **役割**: 認証情報の暗号化・永続化専門クラス（シングルトン）
- **テストしやすい部分**: シングルトンパターン、暗号化/復号化の委譲
- **テストが困難な部分**: Windows DPAPI依存の暗号化処理
- **モック対象**: `utils.crypto`、`core.data_store`

#### DataStore (`core/data_store.py`)
- **役割**: SQLiteデータベースによるデータ永続化
- **テストしやすい部分**: CRUD操作、マイグレーションロジック
- **テストが困難な部分**: データベースファイルロック
- **テスト手法**: 一時ファイルでのテスト分離

#### UnifiedErrorHandler (`core/error_handler.py`)
- **役割**: 統合エラーハンドリング、API認証エラーの統一処理
- **テストしやすい部分**: エラー分類ロジック、静的メソッド
- **テストが困難な部分**: wxPython UIダイアログ表示
- **モック対象**: `wx.MessageBox`

### GUIコンポーネントのテスト戦略

#### 現状の課題
- wxPython UIへの直接依存
- イベント駆動アーキテクチャの複雑性
- 画面読み上げソフトウェアとの相互作用

#### 推奨改善策
1. **MVPパターンの導入**: ビジネスロジックとUI表示の分離
2. **イベントハンドラーの単体テスト**: UI要素から独立したロジックのテスト
3. **モックビューの活用**: 実際のUI描画を伴わないテスト

## 実装計画

### Phase 1: 緊急修正（1-2週間）

#### 目標
- テスト成功率を62%から80%以上に改善
- CI/CDパイプラインでの安定したテスト実行

#### タスク
1. **既存テストの修正**
   - エラーメッセージの期待値を実装に合わせて修正
   - URL正規表現パターンの修正
   - 非同期処理テストの同期処理改善

2. **モック設定の統一**
   - エラーハンドラーの実際の動作に基づいたモック設定
   - MessageBoxの引数形式の統一

3. **テスト実行環境の安定化**
   - インポートエラーの解決
   - 依存関係の明確化

#### 成果物
- 修正されたテストファイル
- テスト実行結果レポート
- 問題点の文書化

### Phase 2: テスト品質向上（2-3週間）

#### 目標
- pytest移行の開始
- テストカバレッジの可視化
- テストデータ管理の改善

#### タスク
1. **pytest移行準備**
   - `conftest.py`の作成
   - フィクスチャの定義
   - 段階的移行計画の策定

2. **ファクトリパターン導入**
   - `factories/`ディレクトリの作成
   - テストデータ生成の標準化
   - `factory_boy`の導入検討

3. **カバレッジ測定**
   - 現在のテストカバレッジの測定
   - カバレッジレポートの生成
   - カバレッジ改善計画の策定

#### 成果物
- pytest設定ファイル
- テストファクトリクラス
- カバレッジレポート

### Phase 3: アーキテクチャ改善（1-2ヶ月）

#### 目標
- 依存性注入の導入
- GUIテストの改善
- 統合テストの充実

#### タスク
1. **依存性注入の導入**
   - コンストラクタ注入パターンの実装
   - テスト時の依存関係の差し替え
   - シングルトンパターンの見直し

2. **MVPパターンの部分導入**
   - プレゼンター層の分離
   - ビューインターフェースの定義
   - GUI独立のビジネスロジックテスト

3. **統合テストの充実**
   - 認証フローの統合テスト
   - 投稿フローの統合テスト
   - エラー処理フローの統合テスト

#### 成果物
- リファクタリングされたコアコンポーネント
- 新しい統合テストスイート
- アーキテクチャドキュメントの更新

## 期待される効果

### 短期効果（Phase 1完了後）
- テスト成功率の改善（現在62% → 目標80%以上）
- CI/CDパイプラインでの安定したテスト実行
- 開発者の生産性向上

### 中期効果（Phase 2完了後）
- テストの保守性向上
- 新機能開発時のテスト効率向上
- コードカバレッジの可視化

### 長期効果（Phase 3完了後）
- リファクタリングの安全性向上
- 新機能開発時のリグレッション防止
- コードの保守性向上
- アーキテクチャの改善

## リスクと対策

### リスク
1. **既存機能への影響**: リファクタリング時の機能破綻
2. **開発リソース**: テスト改善に必要な工数
3. **学習コスト**: 新しいテストフレームワークの習得

### 対策
1. **段階的な移行**: 既存テストを維持しながら段階的に改善
2. **優先順位の明確化**: 重要なコンポーネントから順次対応
3. **ドキュメント整備**: 移行手順と新しい手法の文書化

## まとめ

この戦略により、SSkyプロジェクトのテスト品質を体系的に改善し、持続可能で効率的なテスト環境を構築できます。特に、GUI依存を最小化し、ビジネスロジックを中心としたテスト設計により、長期的な保守性を確保できます。

段階的な実装により、既存の開発フローを維持しながら、着実にテスト品質を向上させることが可能です。