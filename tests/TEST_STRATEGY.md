# SSky テスト戦略ドキュメント

## 概要
このドキュメントは、SSkyプロジェクトのテスト戦略とガイドラインを定義します。

## テストピラミッド

### 単体テスト (70-80%)
**目的**: 個々のコンポーネントとビジネスロジックの検証

**対象**:
- コアモジュール (core/)
  - APIクライアント
  - 認証マネージャー
  - データストア
  - エラーハンドラー
- ユーティリティ (utils/)
  - 時間フォーマット
  - URL処理
  - 暗号化
- 設定管理 (config/)

**原則**:
- 外部依存はモック化
- 高速実行（各テスト < 100ms）
- 独立性の保証

### 統合テスト (15-25%)
**目的**: コンポーネント間の連携検証

**対象**:
- 認証フロー（ログイン→セッション管理→API呼び出し）
- 投稿フロー（作成→送信→表示）
- 設定フロー（変更→保存→反映）
- エラーハンドリングフロー

**原則**:
- 実際のコンポーネント連携を検証
- 外部APIはモック化
- データベースはテスト用インスタンス使用

### E2Eテスト (5-10%)
**目的**: ユーザー視点での主要機能の検証

**対象**:
- アプリケーション起動・終了
- ログインから投稿までの基本フロー
- タイムライン表示と更新
- 設定変更の反映

**原則**:
- 実際のGUIを使用
- 重要なユーザーパスのみカバー
- スモークテストとして活用

## テストフレームワーク

### 統一方針
- **フレームワーク**: pytest
- **モック**: pytest-mock + unittest.mock
- **カバレッジ**: pytest-cov
- **並列実行**: pytest-xdist

### 移行計画
1. 既存のunittestテストをpytestに移行
2. 重複テストファイルの統合
3. 命名規則の統一

## ディレクトリ構造

```
tests/
├── conftest.py                 # グローバル設定
├── pytest.ini                  # pytest設定
├── unit/                       # 単体テスト
│   ├── core/
│   ├── gui/
│   ├── utils/
│   └── config/
├── integration/                # 統合テスト
├── e2e/                       # E2Eテスト
├── contract/                  # API契約テスト
├── performance/               # パフォーマンステスト
├── fixtures/                  # テストデータ
├── factories/                 # テストファクトリ
└── mocks/                    # 共通モック
```

## テスト命名規則

### ファイル名
- `test_<module_name>.py`
- 例: `test_api_client.py`

### テスト関数名
- `test_<機能>_<条件>_<期待結果>`
- 例: `test_login_valid_credentials_success`

### テストクラス名
- `Test<ClassName>`
- 例: `TestBlueskyApiClient`

## モックとフィクスチャ

### モック戦略
- **外部API**: 常にモック化
- **データベース**: テスト用インメモリDB使用
- **ファイルシステム**: tmpディレクトリ使用
- **時間**: freezegun使用

### フィクスチャ管理
```python
# conftest.py
@pytest.fixture
def api_client():
    """APIクライアントのフィクスチャ"""
    return BlueskyApiClient()

@pytest.fixture
def mock_session():
    """モックセッションのフィクスチャ"""
    return MagicMock(spec=Session)
```

## カバレッジ目標

### 全体目標
- **ライン カバレッジ**: 80%以上
- **ブランチ カバレッジ**: 70%以上

### モジュール別目標
| モジュール | ライン | ブランチ |
|-----------|--------|----------|
| core/     | 90%    | 80%      |
| utils/    | 95%    | 90%      |
| config/   | 85%    | 75%      |
| gui/      | 70%    | 60%      |

## CI/CD統合

### GitHub Actions
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12', '3.13']
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run unit tests
      run: pytest tests/unit --cov --cov-report=xml
    
    - name: Run integration tests
      run: pytest tests/integration -v
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## テスト実行コマンド

### 基本コマンド
```bash
# 全テスト実行
pytest

# 単体テストのみ
pytest tests/unit

# カバレッジ付き実行
pytest --cov=. --cov-report=html

# 並列実行
pytest -n auto

# マーカー指定実行
pytest -m "not slow"
```

### 開発時コマンド
```bash
# ファイル監視モード
pytest-watch

# 失敗テストのみ再実行
pytest --lf

# デバッグモード
pytest -vvs --pdb
```

## ベストプラクティス

### DO
- ✅ テストは独立して実行可能にする
- ✅ 明確で説明的なテスト名を使用
- ✅ AAA (Arrange-Act-Assert) パターンを使用
- ✅ テストデータはファクトリで生成
- ✅ 共通処理はフィクスチャ化

### DON'T
- ❌ テスト間で状態を共有しない
- ❌ 実際の外部APIを呼び出さない
- ❌ ハードコードされた値を使用しない
- ❌ sleep()を使用しない（時間依存のテスト）
- ❌ 巨大なテスト関数を作成しない

## テストデータ管理

### ファクトリパターン
```python
# factories/post_factory.py
class PostFactory:
    @staticmethod
    def create(**kwargs):
        defaults = {
            'text': 'テスト投稿',
            'created_at': datetime.now(),
            'author': UserFactory.create()
        }
        defaults.update(kwargs)
        return Post(**defaults)
```

### フィクスチャデータ
```json
// fixtures/sample_posts.json
{
  "posts": [
    {
      "id": "1",
      "text": "サンプル投稿",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

## トラブルシューティング

### よくある問題

#### シングルトンのリセット
```python
@pytest.fixture(autouse=True)
def reset_singletons():
    """各テスト前にシングルトンをリセット"""
    SettingsManager._instance = None
    yield
    SettingsManager._instance = None
```

#### Windows固有の問題
```python
@pytest.mark.skipif(
    sys.platform != "win32",
    reason="Windows専用テスト"
)
def test_windows_specific_feature():
    pass
```

## 更新履歴

- 2025-01-12: 初版作成
- テスト戦略の定義
- ディレクトリ構造の設計
- CI/CD統合の計画