#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
カバレッジレポート生成スクリプト (Phase 2)
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
import argparse


def run_command(command, description):
    """コマンドを実行し、結果を表示"""
    print(f"\n{'='*60}")
    print(f"実行中: {description}")
    print(f"コマンド: {' '.join(command)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=Path(__file__).parent.parent
        )
        print(result.stdout)
        if result.stderr:
            print("WARNING:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="SSky カバレッジレポート生成")
    parser.add_argument(
        "--test-type", 
        choices=["unit", "integration", "all"], 
        default="all",
        help="実行するテストの種類"
    )
    parser.add_argument(
        "--format", 
        choices=["term", "html", "xml", "json", "all"], 
        default="all",
        help="出力フォーマット"
    )
    parser.add_argument(
        "--min-coverage", 
        type=float, 
        default=80.0,
        help="最小カバレッジ閾値（パーセント）"
    )
    parser.add_argument(
        "--parallel", 
        action="store_true",
        help="並列テスト実行"
    )
    
    args = parser.parse_args()
    
    print(f"""
SSky カバレッジレポート生成
============================
テストタイプ: {args.test_type}
出力フォーマット: {args.format}
最小カバレッジ: {args.min_coverage}%
並列実行: {'有効' if args.parallel else '無効'}
開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
    
    # テスト対象ディレクトリの決定
    if args.test_type == "unit":
        test_dirs = ["tests/unit"]
    elif args.test_type == "integration":
        test_dirs = ["tests/integration"]
    else:
        test_dirs = ["tests/unit", "tests/integration"]
    
    # 基本的なpytestコマンドの構築
    pytest_cmd = ["python", "-m", "pytest"]
    pytest_cmd.extend(test_dirs)
    pytest_cmd.extend(["--cov=core", "--cov=utils", "--cov=config"])
    
    # 並列実行オプション
    if args.parallel:
        pytest_cmd.extend(["-n", "auto"])
    
    # 詳細出力
    pytest_cmd.extend(["-v", "--tb=short"])
    
    # カバレッジレポート形式の指定
    if args.format in ["term", "all"]:
        pytest_cmd.append("--cov-report=term-missing")
    
    if args.format in ["html", "all"]:
        pytest_cmd.append("--cov-report=html:htmlcov")
    
    if args.format in ["xml", "all"]:
        pytest_cmd.append("--cov-report=xml")
    
    if args.format in ["json", "all"]:
        # pytest-covはjsonレポートをサポートしていないため、後で coverage json を実行
        pass
    
    # 最小カバレッジ閾値の設定
    pytest_cmd.extend([f"--cov-fail-under={args.min_coverage}"])
    
    # テストの実行
    success = run_command(pytest_cmd, "pytestとカバレッジ測定の実行")
    
    if not success:
        print("\n❌ テストまたはカバレッジ測定が失敗しました")
        return 1
    
    # JSONレポートの生成（必要な場合）
    if args.format in ["json", "all"]:
        json_cmd = ["python", "-m", "coverage", "json"]
        run_command(json_cmd, "JSONカバレッジレポートの生成")
    
    # カバレッジレポートの表示
    if args.format in ["html", "all"]:
        html_path = Path(__file__).parent.parent / "htmlcov" / "index.html"
        if html_path.exists():
            print(f"\n📊 HTMLカバレッジレポート: {html_path.absolute()}")
    
    if args.format in ["xml", "all"]:
        xml_path = Path(__file__).parent.parent / "coverage.xml"
        if xml_path.exists():
            print(f"📄 XMLカバレッジレポート: {xml_path.absolute()}")
    
    if args.format in ["json", "all"]:
        json_path = Path(__file__).parent.parent / "coverage.json"
        if json_path.exists():
            print(f"📋 JSONカバレッジレポート: {json_path.absolute()}")
    
    # 完了メッセージ
    print(f"""
✅ カバレッジレポート生成完了
完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
    
    return 0


if __name__ == "__main__":
    exit(main())