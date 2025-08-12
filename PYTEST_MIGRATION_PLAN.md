# SSky Pytest移行計画

## 現状分析

### 現在のテスト環境
- **テストフレームワーク**: unittest + 一部pytest
- **テストランナー**: `tests/run_tests.py` (unittest.TextTestRunner)
- **既存テスト数**: 107テスト
- **成功率**: 100%

### 既存のpytest対応状況
#### ✅ 既にpytest対応済み
- `tests/pytest.ini` - 設定ファイル完備
- `tests/conftest.py` - グローバルフィクスチャ定義済み
- `tests/unit/core/client/test_api_client.py`
- `tests/unit/core/test_api_client_pytest.py`
- `tests/unit/utils/test_auth_decorators_pytest.py`
- `tests/unit/utils/test_time_format_pytest.py`

#### ❌ unittest形式のままのファイル（移行対象）
1. `tests/test_api_client.py`
2. `tests/test_auth_decorators.py`
3. `tests/test_data_store.py`
4. `tests/test_error_handler.py`
5. `tests/test_settings_manager.py`
6. `tests/test_time_format.py`
7. `tests/run_tests.py` (テストランナー)

## 移行戦略

### Phase 1: 環境準備（即座実行）
1. **requirements-test.txtの作成**
   ```txt
   pytest==8.3.4
   pytest-cov==5.0.0
   pytest-mock==3.14.0
   pytest-xdist==3.6.1
   pytest-timeout==2.3.1
   pytest-watch==4.2.0
   freezegun==1.5.1
   ```

2. **pytest.ini最適化**
   - カバレッジ設定の調整
   - マーカー定義の確認
   - 実行オプションの最適化

### Phase 2: unittest → pytest変換（優先度高）

#### 変換パターン例
```python
# Before (unittest)
class TestBlueskyApiClient(unittest.TestCase):
    def setUp(self):
        self.client = BlueskyApiClient()
    
    def test_login(self):
        self.assertTrue(self.client.login())

# After (pytest)
class TestBlueskyApiClient:
    @pytest.fixture
    def client(self):
        return BlueskyApiClient()
    
    def test_login(self, client):
        assert client.login() is True
```

#### 移行対象ファイルと作業内容

| ファイル | 行数 | 複雑度 | 優先度 |
|---------|------|--------|--------|
| test_api_client.py | 250+ | 高 | 1 |
| test_data_store.py | 150+ | 中 | 2 |
| test_error_handler.py | 100+ | 中 | 3 |
| test_auth_decorators.py | 200+ | 高 | 4 |
| test_settings_manager.py | 120+ | 低 | 5 |
| test_time_format.py | 80+ | 低 | 6 |

### Phase 3: テスト構造の最適化

#### 1. 重複テストの統合
- `tests/test_*.py` → `tests/unit/` へ移動
- pytest版と unittest版の重複を解消

#### 2. フィクスチャの共通化
```python
# tests/conftest.py に追加
@pytest.fixture(scope="session")
def test_database():
    """テスト用データベース"""
    ...

@pytest.fixture
def authenticated_client():
    """認証済みクライアント"""
    ...
```

#### 3. テストマーカーの活用
```python
@pytest.mark.unit
@pytest.mark.windows
def test_windows_specific_feature():
    ...

@pytest.mark.integration
@pytest.mark.slow
def test_full_workflow():
    ...
```

### Phase 4: CI/CD統合

#### GitHub Actions設定
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
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests with coverage
      run: |
        pytest --cov=. --cov-report=xml --cov-report=term
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
```

### Phase 5: 実行コマンドの更新

#### CLAUDE.mdの更新
```cmd
# 旧コマンド
python tests\run_tests.py

# 新コマンド
pytest

# カバレッジ付き
pytest --cov --cov-report=html

# 特定のテストのみ
pytest tests/unit -v

# 並列実行
pytest -n auto
```

## 実装手順

### Step 1: 環境準備（今すぐ実行）
```bash
# requirements-test.txt作成
# pytestインストール
pip install -r requirements-test.txt
```

### Step 2: 最小限の動作確認
```bash
# 既存のpytestテストが動作するか確認
pytest tests/unit -v
```

### Step 3: 段階的移行
1. 小さなテストファイルから開始（test_time_format.py）
2. アサーションの変換
   - `self.assertEqual(a, b)` → `assert a == b`
   - `self.assertTrue(x)` → `assert x`
   - `self.assertRaises(Ex)` → `pytest.raises(Ex)`
3. setUp/tearDownをfixtureに変換
4. テスト実行して動作確認

### Step 4: 完全移行
1. 全テストファイルの変換完了
2. run_tests.py の廃止
3. pytestコマンドへの完全移行

## メリット

### 開発効率の向上
- ✅ より簡潔なテストコード
- ✅ 強力なアサーション機能
- ✅ 豊富なプラグインエコシステム
- ✅ 並列実行による高速化

### 保守性の向上
- ✅ フィクスチャによる DRY 原則
- ✅ パラメータ化テストの簡易化
- ✅ より良いエラーメッセージ
- ✅ テストのスコープ管理

### CI/CD統合の改善
- ✅ 標準的なツールチェーン
- ✅ カバレッジ統合の簡易化
- ✅ レポート生成の自動化

## リスクと対策

### リスク
1. **移行中のテスト品質低下**
   - 対策: 段階的移行、両フレームワーク並行運用

2. **既存CI/CDパイプラインへの影響**
   - 対策: 新旧コマンドの互換性維持期間設定

3. **チーム学習コスト**
   - 対策: pytest基本パターンのドキュメント化

## タイムライン

| 週 | タスク | 成果物 |
|----|--------|--------|
| Week 1 | 環境準備・小規模ファイル移行 | 2-3ファイル移行完了 |
| Week 2 | 中規模ファイル移行 | 主要テスト移行完了 |
| Week 3 | CI/CD統合・最適化 | 完全pytest環境稼働 |
| Week 4 | ドキュメント更新・改善 | 移行完了 |

## 成功指標

- ✅ 全テストのpytest移行完了
- ✅ カバレッジ80%以上維持
- ✅ テスト実行時間20%短縮
- ✅ CI/CD完全統合
- ✅ 開発者満足度向上

## 次のアクション

1. この計画の承認
2. requirements-test.txt作成
3. 最初のテストファイル移行開始
4. 段階的な全体移行実施