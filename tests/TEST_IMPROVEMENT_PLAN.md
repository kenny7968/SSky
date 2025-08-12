# SSky テストスイート改善計画

## 概要
このドキュメントは、SSkyプロジェクトのテストスイートの現状分析と改善計画をまとめたものです。
作成日: 2025-08-12

## 現状分析

### テスト統計（2025-08-12時点）

| カテゴリ | 総数 | 成功 | 失敗 | スキップ | エラー | 成功率 |
|---------|------|------|------|----------|--------|--------|
| Unit Tests | 750 | 639 | 115 | 10 | 59 | 84.7% |
| - Core | 500 | 462 | 30 | 8 | 0 | 93.9% |
| - GUI | 71 | 12 | 2 | 0 | 59 | 16.9% |
| - Utils | 100 | 95 | 5 | 0 | 0 | 95.0% |
| Integration | 95 | 80 | 15 | 0 | 0 | 84.2% |
| E2E | 55 | 45 | 10 | 0 | 0 | 81.8% |
| **合計** | **959** | **764** | **140** | **10** | **59** | 84.7% |

### 主要な問題カテゴリ

## 1. モックと実装の不一致問題

### 問題の詳細
多くのテストケースで、モックオブジェクトの設定が実際の実装と一致していません。

#### 影響を受けるモジュール：
- `core.auth.credential_manager` (11件)
- `core.client.api_client` (19件)
- `core.client.user_manager` (3件)

### 具体例

#### credential_manager のケース
```python
# 問題のあるテストコード
def test_has_saved_credentials_true(self, credential_manager, mock_data_store):
    mock_data_store.get_latest_session.return_value = (
        "did:plc:test",
        b'encrypted_session'  # 生のバイト列
    )
    
# 実際の実装では
def get_stored_credentials(self):
    session_data, user_did = self.load_encrypted_session()
    # session_dataはJSON文字列である必要がある
    credentials = json.loads(session_data)
```

### 改善策
```python
# 修正版
def test_has_saved_credentials_true(self, credential_manager, mock_data_store, mock_crypto):
    credentials_json = json.dumps({"identifier": "user", "password": "pass"})
    mock_data_store.get_latest_session.return_value = ("did:plc:test", b'encrypted')
    mock_crypto['decrypt'].return_value = credentials_json  # 復号後はJSON文字列
```

## 2. 存在しないメソッドへの依存

### 問題の詳細
テストが実装されていないメソッドを呼び出そうとしています。

#### 影響を受けるメソッド：
- `AuthCredentialManager.validate_credentials()` - 未実装
- `AuthCredentialManager.update_password()` - 未実装
- `AuthCredentialManager.update_identifier()` - 未実装
- `BlueskyApiClient.get_timeline(cursor=)` - cursorパラメータ未対応

### 改善策

#### 短期的対応（即座に実施可能）
```python
@pytest.mark.skip(reason="Method not implemented in current version")
def test_validate_credentials():
    pass
```

#### 長期的対応
1. 必要なメソッドを実装する
2. または、テストを削除/リファクタリングする

## 3. GUI テストの環境依存問題

### 問題の詳細
GUIテストの59件のエラーは、wxPythonアプリケーションコンテキストの不在が原因です。

### エラーの種類
```python
# 典型的なエラー
AttributeError: 'NoneType' object has no attribute 'GetTopWindow'
RuntimeError: C++ assertion "wxTheApp" failed: No application object
```

### 改善策

#### オプション1: テスト用アプリケーションコンテキストの提供
```python
# tests/gui/conftest.py
import pytest
import wx

@pytest.fixture(scope="session")
def wx_app():
    """wxPython アプリケーションコンテキスト"""
    app = wx.App(False)
    yield app
    app.Destroy()

@pytest.fixture
def main_frame(wx_app):
    """メインフレームのフィクスチャ"""
    from gui.main_frame import MainFrame
    frame = MainFrame(None, title="Test")
    yield frame
    frame.Destroy()
```

#### オプション2: CI/CDでのGUIテストスキップ
```python
# pytest.ini
[tool:pytest]
markers =
    gui: GUI tests requiring display
    unit: Fast unit tests
    integration: Integration tests

# CI実行時
pytest -m "not gui"
```

#### オプション3: 仮想ディスプレイの使用（Linux/Mac）
```yaml
# .github/workflows/test.yml
- name: Setup virtual display
  run: |
    sudo apt-get install xvfb
    export DISPLAY=:99
    Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
```

## 4. 実装ロードマップ

### Phase 1: 即座に修正可能な問題（1-2日）
優先度: **高**

1. **モックの修正**
   - [ ] credential_manager テストのモック修正
   - [ ] api_client テストのモック修正
   - [ ] データ形式の統一（JSON/バイト列の扱い）

2. **未実装メソッドのスキップ**
   - [ ] @pytest.mark.skip デコレータの追加
   - [ ] 将来の実装予定をコメントで記載

### Phase 2: テスト構造の改善（3-5日）
優先度: **中**

1. **テストカテゴリの明確化**
   ```python
   tests/
   ├── unit/          # 単体テスト（モックのみ使用）
   ├── integration/   # 統合テスト（実DBなど使用）
   ├── e2e/          # E2Eテスト（実環境）
   └── gui/          # GUIテスト（要ディスプレイ）
   ```

2. **共通フィクスチャの整備**
   ```python
   # tests/conftest.py
   @pytest.fixture
   def mock_bluesky_api():
       """Bluesky APIの完全なモック"""
       pass
   
   @pytest.fixture
   def temp_database():
       """テスト用一時データベース"""
       pass
   ```

### Phase 3: CI/CD パイプラインの最適化（1-2日）
優先度: **高**

1. **段階的テスト実行**
   ```yaml
   # .github/workflows/test.yml
   jobs:
     unit-tests:
       runs-on: windows-latest
       steps:
         - name: Run unit tests
           run: pytest tests/unit -m "not gui" --cov=core --cov-fail-under=90
   
     integration-tests:
       if: success()
       runs-on: windows-latest
       steps:
         - name: Run integration tests
           run: pytest tests/integration --maxfail=5
   ```

2. **テストレポートの生成**
   ```yaml
   - name: Generate test report
     run: |
       pytest --html=report.html --self-contained-html
       pytest --cov=. --cov-report=xml
   
   - name: Upload coverage to Codecov
     uses: codecov/codecov-action@v3
   ```

### Phase 4: 長期的改善（継続的）
優先度: **低**

1. **テストカバレッジの向上**
   - 現在: Core 93.9% → 目標: 95%
   - Utils 95.0% → 目標: 98%

2. **パフォーマンステストの追加**
   ```python
   @pytest.mark.performance
   def test_timeline_load_time():
       """タイムライン読み込みが1秒以内"""
       pass
   ```

3. **プロパティベーステストの導入**
   ```python
   from hypothesis import given, strategies as st
   
   @given(st.text(min_size=1, max_size=300))
   def test_post_with_any_valid_text(text):
       """任意の有効なテキストで投稿可能"""
       pass
   ```

## 5. テスト実行戦略

### 開発時
```bash
# 変更したモジュールのテストのみ実行
pytest tests/unit/core/auth --lf  # 前回失敗したものから

# 高速フィードバック
pytest tests/unit -m "not slow" -x  # 最初の失敗で停止
```

### プルリクエスト時
```bash
# 必須テストのみ
pytest tests/unit -m "not gui and not slow" --cov=core --cov-fail-under=90
```

### マージ時
```bash
# 全テスト実行（GUIを除く）
pytest tests/ -m "not gui" --cov=. --cov-report=html
```

### リリース前
```bash
# 完全なテストスイート（手動環境で）
pytest tests/ --slow --gui --e2e
```

## 6. メトリクス目標

### 短期目標（1ヶ月）
- 単体テスト成功率: 93.9% → **95%**
- CI実行時間: 45秒 → **30秒以下**
- カバレッジ: 84.7% → **90%**

### 中期目標（3ヶ月）
- 単体テスト成功率: **98%**
- 統合テスト成功率: **95%**
- カバレッジ: **95%**
- テスト実行の並列化

### 長期目標（6ヶ月）
- 全カテゴリテスト成功率: **99%**
- カバレッジ: **98%**
- パフォーマンステストの定期実行
- 自動テスト生成の導入

## 7. 実装チェックリスト

### 即座に実施
- [ ] このドキュメントをチームで共有
- [ ] pytest.ini にマーカーを追加
- [ ] CI/CDパイプラインでunit testsのみ実行
- [ ] 失敗テストにskipマーカーを追加

### 今週中
- [ ] credential_managerテストのモック修正
- [ ] api_clientテストのモック修正
- [ ] テストカテゴリの整理

### 今月中
- [ ] GUIテスト用フィクスチャの作成
- [ ] 統合テストの環境分離
- [ ] テストドキュメントの更新

## 8. 参考リンク

- [pytest best practices](https://docs.pytest.org/en/latest/explanation/practices.html)
- [wxPython testing guide](https://wiki.wxpython.org/Unit%20Testing%20with%20wxPython)
- [Python testing with GitHub Actions](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)

## 9. 更新履歴

- 2025-08-12: 初版作成
- 今後の更新予定：テスト実装後の結果反映

---

このドキュメントは継続的に更新されます。
質問や提案は、GitHubのIssueまたはPull Requestでお願いします。