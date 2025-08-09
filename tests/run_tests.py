#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
テスト実行スクリプト (Phase 1 リファクタリング版)
"""

import unittest
import sys
import os
from io import StringIO

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_tests():
    """すべてのテストを実行する"""
    print("SSky テストスイート (Phase 1 リファクタリング版) を実行します...")
    
    # テストディスカバリーを実行
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # テスト実行
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream, 
        verbosity=2,
        buffer=True  # テスト出力をバッファリング
    )
    result = runner.run(suite)
    
    # 結果を標準出力に表示
    output = stream.getvalue()
    print(output)
    
    # テスト結果の要約を表示
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successes = total_tests - failures - errors
    success_rate = (successes / total_tests * 100) if total_tests > 0 else 0
    
    print("\n" + "=" * 70)
    print("テスト結果の要約 (Phase 1 リファクタリング版):")
    print(f"  実行したテスト数: {total_tests}")
    print(f"  成功したテスト数: {successes}")
    print(f"  失敗したテスト数: {failures}")
    print(f"  エラーが発生したテスト数: {errors}")
    print(f"  成功率: {success_rate:.1f}%")
    print("=" * 70)
    
    # 失敗とエラーの詳細を表示
    if failures:
        print("\n失敗したテスト:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.splitlines()[-1] if traceback else 'Unknown failure'}")
    
    if errors:
        print("\nエラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.splitlines()[-1] if traceback else 'Unknown error'}")
    
    # Phase 1 目標達成率を表示
    target_success_rate = 80.0
    print(f"\nPhase 1 目標達成状況:")
    print(f"  目標成功率: {target_success_rate}%")
    print(f"  現在の成功率: {success_rate:.1f}%")
    
    if success_rate >= target_success_rate:
        print("  [OK] Phase 1 目標達成！")
    else:
        remaining = target_success_rate - success_rate
        print(f"  [TARGET] 目標まで残り {remaining:.1f}%")
    
    # 結果に基づいて終了コード設定
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())