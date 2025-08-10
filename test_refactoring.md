# SSky テストリファクタリング計画

## 現状分析

### テストスイート現況
- **実行テスト数**: 107テスト
- **成功率**: 100%
- **Phase 1目標**: 達成済み（目標80% → 実際100%）

### 重大なカバレッジギャップ

| コンポーネント | 現在カバレッジ | 重要度 | 状況 |
|---------------|---------------|--------|------|
| `core/client/facade.py` | **31.0%** | 🔴 最重要 | BlueskyClientファサード、614行の大規模クラス |
| `core/client/user_manager.py` | **11.0%** | 🔴 最重要 | ユーザー操作（フォロー・ブロック）未テスト |
| `core/error_handler.py` | **19.2%** | 🟡 重要 | 統合エラーハンドリング未テスト |
| `core/auth/credential_manager.py` | **63.5%** | 🟡 重要 | 暗号化・Phase3機能未テスト |
| `core/client/session_manager.py` | **47.6%** | 🟡 重要 | イベント処理未テスト |
| `core/events.py` | **0.0%** | 🟡 重要 | イベント定義未検証 |
| `core/protocols.py` | **0.0%** | 🟡 重要 | プロトコル定義未検証 |
| **GUI全体** | **0.0%** | 🟡 重要 | GUI専用テスト完全欠落 |

## Phase 2 リファクタリング計画

### 最優先タスク（緊急）

#### 1. コアファサードテスト作成
**ファイル**: `tests/unit/core/client/test_facade.py`
**目標カバレッジ**: 31.0% → **90%+**

```python
# 必須テストケース
class TestBlueskyClientFacade:
    # 依存性注入機能
    def test_dependency_injection_container_integration()
    def test_create_for_testing_factory_method()
    def test_create_with_custom_credential_manager()
    
    # プロパティテスト
    def test_profile_property()
    def test_is_logged_in_property()
    def test_user_did_property()
    
    # イベントハンドリング
    def test_session_change_event_registration()
    def test_session_change_event_removal()
    def test_session_change_event_execution()
    
    # エラーハンドリング統合
    def test_api_error_propagation()
    def test_authentication_error_handling()
    def test_network_error_recovery()
```

#### 2. ユーザー管理テスト作成
**ファイル**: `tests/unit/core/client/test_user_manager.py`
**目標カバレッジ**: 11.0% → **85%+**

```python
# 必須テストケース
class TestBlueskyUserManager:
    # フォロー機能
    def test_follow_user_success()
    def test_follow_user_api_error()
    def test_unfollow_user_success()
    
    # ブロック・ミュート機能
    def test_block_user_success()
    def test_mute_user_success()
    def test_get_blocked_users()
    def test_get_muted_users()
    
    # ユーザー検索
    def test_search_users()
    def test_get_user_profile()
    
    # エラーハンドリング
    def test_api_client_integration()
    def test_network_error_handling()
```

### 高優先タスク

#### 3. 認証管理テスト拡張
**ファイル**: `tests/unit/core/auth/test_credential_manager_comprehensive.py`
**目標カバレッジ**: 63.5% → **90%+**

```python
# Phase 3新機能テスト
class TestAuthCredentialManagerPhase3:
    def test_save_credentials_convenience_method()
    def test_get_stored_credentials()
    def test_clear_credentials()
    
    # 暗号化エラーケース
    def test_encryption_failure_handling()
    def test_decryption_failure_handling()
    def test_json_conversion_error()
    
    # 依存性注入（Phase 3追加）
    def test_dependency_injection_integration()
```

#### 4. エラーハンドリングテスト
**ファイル**: `tests/unit/core/test_error_handler_comprehensive.py`
**目標カバレッジ**: 19.2% → **80%+**

```python
class TestUnifiedErrorHandlerComprehensive:
    # エラー分類・レベル判定
    def test_error_level_determination()
    def test_error_categorization()
    
    # UI統合（モック使用）
    def test_show_error_dialog_integration()
    def test_error_message_formatting()
    
    # 認証エラー特別処理
    def test_authentication_error_special_handling()
    def test_session_expired_handling()
    
    # 再試行ロジック
    def test_retry_logic()
    def test_timeout_handling()
```

### 中優先タスク

#### 5. セッション管理テスト
**ファイル**: `tests/unit/core/client/test_session_manager_comprehensive.py`
**目標カバレッジ**: 47.6% → **80%+**

#### 6. イベント・プロトコルテスト
**ファイル**: `tests/unit/core/test_events.py`
**ファイル**: `tests/unit/core/test_protocols.py`
**目標カバレッジ**: 0.0% → **70%+**

### GUI テスト新規作成

#### 7. GUI基底コンポーネントテスト
**ディレクトリ**: `tests/unit/gui/`

```python
# tests/unit/gui/test_main_frame.py
class TestMainFrame:
    def test_menu_system_initialization()
    def test_timeline_view_integration()
    def test_auth_state_ui_updates()

# tests/unit/gui/dialogs/test_dialog_base.py
class TestBaseDialog:
    def test_validation_framework()
    def test_error_message_display()
    def test_modal_behavior()

# tests/unit/gui/timeline/test_timeline_view.py
class TestTimelineView:
    def test_auto_refresh_functionality()
    def test_data_display_updates()
    def test_screen_reader_accessibility()
```

### 統合・E2Eテスト強化

#### 8. GUI統合テスト
**ファイル**: `tests/integration/test_gui_integration.py`

```python
class TestGUIIntegration:
    def test_complete_login_flow()
    def test_post_creation_to_display_flow()
    def test_error_ui_display()
    def test_session_management_ui_sync()
```

#### 9. エンドツーエンドテスト
**ファイル**: `tests/e2e/test_complete_user_scenarios.py`

```python
class TestCompleteUserScenarios:
    def test_first_launch_to_login()
    def test_timeline_browsing_to_posting()
    def test_user_operations_follow_block()
    def test_settings_change_and_restart()
```

### セキュリティテスト

#### 10. セキュリティテスト新規作成
**ファイル**: `tests/security/test_crypto_operations.py`

```python
class TestCryptoSecurity:
    def test_dpapi_encryption_failure_recovery()
    def test_malicious_session_detection()
    def test_input_validation_and_sanitization()
    def test_credential_storage_security()
```

## 実装スケジュール

### Week 1: 最重要コンポーネント
- [ ] `test_facade.py` - BlueskyClientファサード
- [ ] `test_user_manager.py` - ユーザー管理機能

### Week 2: 高優先コンポーネント  
- [ ] `test_credential_manager_comprehensive.py` - 認証管理拡張
- [ ] `test_error_handler_comprehensive.py` - エラーハンドリング

### Week 3: GUI基底テスト
- [ ] `test_main_frame.py` - メインフレーム
- [ ] `test_dialog_base.py` - ダイアログ基底
- [ ] `test_timeline_view.py` - タイムライン表示

### Week 4: 統合・E2Eテスト
- [ ] `test_gui_integration.py` - GUI統合テスト
- [ ] `test_complete_user_scenarios.py` - E2Eシナリオ

## 品質目標

### カバレッジ目標
- **重要ファサード・マネージャークラス**: 90%以上
- **インフラストラクチャクラス**: 80%以上  
- **GUI基底コンポーネント**: 70%以上
- **統合テスト**: 包括的なシナリオカバー

### テスト品質指標
- **単体テスト**: 各クラスの全パブリックメソッド
- **統合テスト**: コンポーネント間連携
- **エラーケース**: 全ての例外パターン
- **エッジケース**: 境界値・異常系

## リスク管理

### 高リスクエリア
1. **暗号化処理**: DPAPI依存の認証情報管理
2. **セッション管理**: 並行処理とイベント競合
3. **GUI統合**: wxPython複雑な依存関係
4. **API連携**: 外部サービス依存の不安定性

### 対策
- モック/スタブ戦略の徹底
- テスト環境の独立性確保
- CI/CD統合での自動品質チェック
- 段階的ロールアウト計画

## 成果測定

### Phase 2完了条件
- [ ] 全コアコンポーネント80%以上カバレッジ
- [ ] GUI基本機能70%以上カバレッジ  
- [ ] 統合テスト包括シナリオ完備
- [ ] セキュリティテスト基盤構築
- [ ] CI/CD統合完了

### 継続的改善
- 週次カバレッジレポート
- 新機能追加時の即座テスト作成
- リファクタリング時のテスト先行更新
- 品質メトリクス継続監視