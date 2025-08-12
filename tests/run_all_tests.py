#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - 統一テストランナー
pytestベースの新しいテスト実行システム
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRunner:
    """統一テストランナー"""
    
    def __init__(self, verbose: bool = False, coverage: bool = True):
        self.verbose = verbose
        self.coverage = coverage
        self.project_root = Path(__file__).parent.parent
        self.test_root = self.project_root / "tests"
        
    def run_command(self, cmd: List[str], description: str) -> int:
        """コマンドを実行して結果を返す"""
        print(f"\n{'='*70}")
        print(f"実行中: {description}")
        print(f"{'='*70}")
        
        if self.verbose:
            print(f"コマンド: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, cwd=str(self.project_root))
        return result.returncode
    
    def run_unit_tests(self) -> int:
        """単体テストを実行"""
        cmd = [sys.executable, "-m", "pytest", "tests/unit"]
        
        if self.verbose:
            cmd.append("-vv")
        else:
            cmd.append("-v")
            
        if self.coverage:
            cmd.extend(["--cov=core", "--cov=utils", "--cov=config"])
            cmd.append("--cov-report=term-missing:skip-covered")
            
        cmd.append("-m")
        cmd.append("not slow")
        
        return self.run_command(cmd, "単体テスト")
    
    def run_integration_tests(self) -> int:
        """統合テストを実行"""
        cmd = [sys.executable, "-m", "pytest", "tests/integration"]
        
        if self.verbose:
            cmd.append("-vv")
        else:
            cmd.append("-v")
            
        return self.run_command(cmd, "統合テスト")
    
    def run_e2e_tests(self) -> int:
        """E2Eテストを実行"""
        cmd = [sys.executable, "-m", "pytest", "tests/e2e"]
        
        if self.verbose:
            cmd.append("-vv")
        else:
            cmd.append("-v")
            
        cmd.append("--tb=short")
        
        return self.run_command(cmd, "E2Eテスト")
    
    def run_performance_tests(self) -> int:
        """パフォーマンステストを実行"""
        cmd = [sys.executable, "-m", "pytest", "tests/performance"]
        
        if self.verbose:
            cmd.append("-vv")
        
        cmd.append("--benchmark-only")
        
        return self.run_command(cmd, "パフォーマンステスト")
    
    def run_all(self) -> int:
        """全てのテストを実行"""
        cmd = [sys.executable, "-m", "pytest", "tests"]
        
        if self.verbose:
            cmd.append("-vv")
        else:
            cmd.append("-v")
            
        if self.coverage:
            cmd.extend([
                "--cov=core",
                "--cov=gui", 
                "--cov=utils",
                "--cov=config"
            ])
            cmd.extend([
                "--cov-report=term-missing:skip-covered",
                "--cov-report=html:htmlcov",
                "--cov-report=xml"
            ])
            
        cmd.append("-m")
        cmd.append("not slow")
        
        return self.run_command(cmd, "全テストスイート")
    
    def run_specific_file(self, file_path: str) -> int:
        """特定のテストファイルを実行"""
        cmd = [sys.executable, "-m", "pytest", file_path]
        
        if self.verbose:
            cmd.append("-vv")
        else:
            cmd.append("-v")
            
        return self.run_command(cmd, f"テストファイル: {file_path}")
    
    def run_with_markers(self, markers: List[str]) -> int:
        """マーカー指定でテストを実行"""
        cmd = [sys.executable, "-m", "pytest", "tests"]
        
        if self.verbose:
            cmd.append("-vv")
        else:
            cmd.append("-v")
            
        marker_expr = " and ".join(markers)
        cmd.extend(["-m", marker_expr])
        
        return self.run_command(cmd, f"マーカー: {marker_expr}")
    
    def run_failed_only(self) -> int:
        """前回失敗したテストのみ実行"""
        cmd = [sys.executable, "-m", "pytest", "--lf", "tests"]
        
        if self.verbose:
            cmd.append("-vv")
        else:
            cmd.append("-v")
            
        return self.run_command(cmd, "前回失敗したテスト")
    
    def run_parallel(self, num_workers: Optional[int] = None) -> int:
        """並列実行"""
        cmd = [sys.executable, "-m", "pytest", "tests"]
        
        if num_workers:
            cmd.extend(["-n", str(num_workers)])
        else:
            cmd.extend(["-n", "auto"])
            
        if self.verbose:
            cmd.append("-vv")
        else:
            cmd.append("-v")
            
        return self.run_command(cmd, f"並列実行 (ワーカー: {num_workers or 'auto'})")
    
    def generate_coverage_report(self) -> int:
        """カバレッジレポートを生成"""
        cmd = [sys.executable, "-m", "coverage", "html"]
        result = self.run_command(cmd, "カバレッジレポート生成")
        
        if result == 0:
            html_path = self.project_root / "htmlcov" / "index.html"
            print(f"\nカバレッジレポート: {html_path}")
            
        return result


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="SSky統一テストランナー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python tests/run_all_tests.py              # 全テスト実行
  python tests/run_all_tests.py --unit       # 単体テストのみ
  python tests/run_all_tests.py --integration # 統合テストのみ
  python tests/run_all_tests.py --e2e        # E2Eテストのみ
  python tests/run_all_tests.py --performance # パフォーマンステスト
  python tests/run_all_tests.py --file tests/unit/test_api.py  # 特定ファイル
  python tests/run_all_tests.py --marker unit,fast  # マーカー指定
  python tests/run_all_tests.py --failed     # 前回失敗分のみ
  python tests/run_all_tests.py --parallel   # 並列実行
  python tests/run_all_tests.py --no-cov     # カバレッジなし
        """
    )
    
    # テストタイプ選択
    parser.add_argument("--all", action="store_true", 
                       help="全てのテストを実行（デフォルト）")
    parser.add_argument("--unit", action="store_true",
                       help="単体テストのみ実行")
    parser.add_argument("--integration", action="store_true",
                       help="統合テストのみ実行")
    parser.add_argument("--e2e", action="store_true",
                       help="E2Eテストのみ実行")
    parser.add_argument("--performance", action="store_true",
                       help="パフォーマンステストのみ実行")
    
    # 実行オプション
    parser.add_argument("--file", type=str,
                       help="特定のテストファイルを実行")
    parser.add_argument("--marker", type=str,
                       help="マーカー指定（カンマ区切り）")
    parser.add_argument("--failed", action="store_true",
                       help="前回失敗したテストのみ実行")
    parser.add_argument("--parallel", nargs="?", const="auto", type=str,
                       help="並列実行（オプション: ワーカー数）")
    
    # その他オプション
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="詳細出力")
    parser.add_argument("--no-cov", action="store_true",
                       help="カバレッジ計測を無効化")
    parser.add_argument("--coverage-report", action="store_true",
                       help="カバレッジレポートのみ生成")
    
    args = parser.parse_args()
    
    # TestRunnerインスタンス作成
    runner = TestRunner(
        verbose=args.verbose,
        coverage=not args.no_cov
    )
    
    # カバレッジレポートのみ生成
    if args.coverage_report:
        return runner.generate_coverage_report()
    
    # 実行するテストを決定
    if args.file:
        return runner.run_specific_file(args.file)
    elif args.marker:
        markers = args.marker.split(",")
        return runner.run_with_markers(markers)
    elif args.failed:
        return runner.run_failed_only()
    elif args.parallel:
        workers = None
        if args.parallel != "auto":
            try:
                workers = int(args.parallel)
            except ValueError:
                print(f"警告: 無効なワーカー数 '{args.parallel}', autoを使用します")
        return runner.run_parallel(workers)
    elif args.unit:
        return runner.run_unit_tests()
    elif args.integration:
        return runner.run_integration_tests()
    elif args.e2e:
        return runner.run_e2e_tests()
    elif args.performance:
        return runner.run_performance_tests()
    else:
        # デフォルトは全テスト実行
        return runner.run_all()


if __name__ == "__main__":
    sys.exit(main())