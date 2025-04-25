# SSky - Bluesky Client (Developer Information)

## これは開発バージョンです This is a Development Version

SSkyは現在開発中バージョンです。多数の未実装機能やバグを含みます。

SSky is currently in development version. It contains many unimplemented features and bugs.

## 生成AI利用について About the Use of Generative AI

SSkyはCline+Claude3.7 SONNETを全面的に利用して開発しています。

SSky is developed with full utilization of Cline+Claude3.7 SONNET.

## 概要 Overview

SSkyは、Blueskyのためのシンプルで使いやすい、スクリーンリーダーに最適化されたWindowsクライアントアプリケーションです。Blueskyの投稿の閲覧、投稿、いいね、返信などの基本的な操作を行うことができます。

SSky is a simple and easy-to-use Windows client application for Bluesky, optimized screen reader. You can perform basic operations such as viewing posts, posting, liking, and replying on Bluesky.

## 開発環境・言語 Development Environment & Language

- OS: Windows
- 言語 / Language: Python 3.13.2
- GUI: wxPython
- ビルドツール / Build Tool: PyInstaller
- パッケージングツール / Packaging Tool: SCons
- 依存関係管理 / Dependency Management: pipreqs

## 動作環境 Operating Environment

- OS: Windows 11
- 必要なソフトウェア / Required Software: なし（スタンドアロンアプリケーション） / None (standalone application)

## 必要なライブラリ Required Libraries

主な依存ライブラリ Main dependency libraries:

- atproto==0.0.61 - Bluesky API client
- pywin32==310 - DPAPI access
- wxPython - GUI framework
- PyInstaller - Build tool
- SCons - Packaging tool

## 開発環境のセットアップ Development Environment Setup

1. Python 3.13.2をインストール / Install Python 3.13.2
2. 必要なライブラリをインストール / Install required libraries

```cmd
pip install -r requirements.txt
pip install wxPython
pip install pyinstaller
pip install scons
pip install pipreqs
```

3. (オプション) pre-commitのセットアップ / (Optional) Set up pre-commit
   - プロジェクトには.pre-commit-configファイルが用意されています / The project has a .pre-commit-config file
   - コード品質を維持するために、pre-commitを導入することをお勧めします / We recommend introducing pre-commit to maintain code quality

```cmd
pip install pre-commit
pre-commit install
```

## 開発方法 Development Method

### アプリケーションの実行（開発モード） Running the Application (Development Mode)

```cmd
python SSky.py
```

### 依存関係の更新 Updating Dependencies

プロジェクトの依存関係を更新するには、以下のコマンドを実行します：
To update project dependencies, run the following command:

```cmd
make-requirements.bat
```

または / or

```cmd
pipreqs .\ --encoding=utf-8 --savepath requirements.txt --force
```

### テストの実行 Running Tests

```cmd
python tests\run_tests.py
```

## ビルド方法 Build Method

### 実行可能ファイルのビルド Building Executable Files

Pyinstaller を使用して実行可能なexeファイルを作成します。
Create an executable exe file using Pyinstaller.

```cmd
pyinstaller --name SSky --noconsole --onedir --noupx --clean --noconfirm --log-level=INFO SSky.py
```

ビルドされたexeファイルが Windows Defender でウイルス検知される場合は、ソースコードからビルドした Pyinstaller を利用してください。
If the built exe file is detected as a virus by Windows Defender, please use Pyinstaller built from source code.

```cmd
pip uninstall -y pyinstaller
pip install wheel
git clone https://github.com/pyinstaller/pyinstaller.git # PyInstallerのソースをクローン / Clone PyInstaller source
cd pyinstaller\bootloader
python .\waf distclean all
cd ..
pip install .
```

### パッケージング Packaging

SCons を使用してzipファイルにパッケージングします。バージョン番号を指定する必要があります：
Package into a zip file using SCons. You need to specify a version number:

```
scons --release=1.0.0
```

このコマンドは以下の処理を行います：
This command performs the following processes:

1. PyInstallerを使用してSSky.pyをビルド / Build SSky.py using PyInstaller
2. 必要なファイル（マニュアル、changelog.mdなど）をパッケージディレクトリにコピー / Copy necessary files (manual, changelog.md, etc.) to the package directory
3. zipファイルを作成 / Create a zip file

ビルド結果は以下の場所に生成されます：
Build results are generated in the following locations:

- Package directory: `build/SSky-{version}/`
- zip file: `release/SSky-{version}.zip`

## アーキテクチャ Architecture

SSkyは以下のコンポーネントで構成されています：
SSky consists of the following components:

- **コア (core/)**: Bluesky APIとの通信、認証管理、データ保存などの基本機能を提供
  - **client.py**: Bluesky APIのラッパー、タイムライン取得や投稿などの機能を提供
  - **data_store.py**: ユーザーデータの永続化を担当
  - **auth/auth_manager.py**: 認証情報の管理と暗号化を担当

- **GUI (gui/)**: ユーザーインターフェース
  - **main_frame.py**: メインウィンドウの実装
  - **timeline_view.py**: タイムラインの表示と操作
    - **TimelineView**: タイムラインパネルの実装、自動更新機能と時間表示更新機能を含む
    - **TimelineListCtrl**: 実際の投稿リストを表示するリストコントロール
  - **dialogs/**: 各種ダイアログの実装
    - **post_detail_dialog.py**: 投稿詳細表示ダイアログ
    - **login_dialog.py**: ログインダイアログ
    - **post_dialog.py**: 投稿作成ダイアログ
    - **reply_dialog.py**: 返信作成ダイアログ
    - **quote_dialog.py**: 引用作成ダイアログ
  - **handlers/**: イベントハンドラの実装
    - **auth_handlers.py**: 認証関連のイベント処理
    - **post_handlers.py**: 投稿関連のイベント処理

- **ユーティリティ (utils/)**: 共通機能
  - **crypto.py**: 認証情報の暗号化・復号化
  - **file_utils.py**: ファイル操作
  - **time_format.py**: 時間フォーマット
  - **url_utils.py**: URL操作と検出

- **設定 (config/)**: アプリケーション設定
  - **app_config.py**: アプリケーション設定の管理
  - **logging_config.py**: ロギング設定
  - **settings_manager.py**: ユーザー設定の管理

- **Core (core/)**: Provides basic functionality such as communication with Bluesky API, authentication management, and data storage
  - **client.py**: Wrapper for Bluesky API, provides functions for timeline retrieval, posting, etc.
  - **data_store.py**: Responsible for persisting user data
  - **auth/auth_manager.py**: Manages authentication information and encryption

- **GUI (gui/)**: User interface
  - **main_frame.py**: Implementation of the main window
  - **timeline_view.py**: Display and operation of timeline
    - **TimelineView**: Implementation of timeline panel, including automatic update and time display update functions
    - **TimelineListCtrl**: List control that displays the actual post list
  - **dialogs/**: Implementation of various dialogs
    - **post_detail_dialog.py**: Post detail display dialog
    - **login_dialog.py**: Login dialog
    - **post_dialog.py**: Post creation dialog
    - **reply_dialog.py**: Reply creation dialog
    - **quote_dialog.py**: Quote creation dialog
  - **handlers/**: Implementation of event handlers
    - **auth_handlers.py**: Authentication-related event processing
    - **post_handlers.py**: Post-related event processing

- **Utilities (utils/)**: Common functions
  - **crypto.py**: Encryption and decryption of authentication information
  - **file_utils.py**: File operations
  - **time_format.py**: Time formatting
    - **format_relative_time**: Relative time display ("just now", "10 minutes ago", etc.)
    - **format_timestamp_to_jst**: Convert UTC timestamp to Japan time
  - **url_utils.py**: URL operations and detection

- **Configuration (config/)**: Application settings
  - **app_config.py**: Management of application settings
  - **logging_config.py**: Logging settings
  - **settings_manager.py**: Management of user settings

## 主要クラス Main Classes

- **SSkyApp**: アプリケーションのメインクラス
- **MainFrame**: メインウィンドウ
- **TimelineView**: タイムラインの表示と操作
- **BlueskyClient**: Bluesky APIのラッパー
- **AuthManager**: 認証情報の管理
- **AppConfig**: アプリケーション設定の管理

- **SSkyApp**: Main application class
- **MainFrame**: Main window
- **TimelineView**: Display and operation of timeline
- **BlueskyClient**: Wrapper for Bluesky API
- **AuthManager**: Management of authentication information
- **AppConfig**: Management of application settings

## ライセンス License

このプロジェクトのライセンスについては、LICENSEファイルを参照してください。
For the license of this project, please refer to the LICENSE file.

## 連絡先・バグ報告 Contact & Bug Reports

バグや機能要望などがある場合は、GitHubリポジトリにissueを立ててください。
プルリクエストも歓迎です。その際はdevelopブランチにプルリクエストしてください。

If you have any bugs or feature requests, please create an issue on the GitHub repository.
Pull requests are also welcome. Please make pull requests to the develop branch.
