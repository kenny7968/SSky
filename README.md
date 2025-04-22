# SSky - Blueskyクライアント（開発者向け情報）

SSkyは、Blueskyのためのシンプルで使いやすいWindowsクライアントアプリケーションです。Tween風の操作感で、Blueskyの投稿の閲覧や投稿、いいね、返信などの基本的な操作を行うことができます。

## 開発環境・言語

- 言語: Python 3.13.2
- GUI: wxPython
- ビルドツール: PyInstaller
- パッケージングツール: SCons
- 依存関係管理: pipreqs

## 動作環境

- OS: Windows 10/11
- 必要なソフトウェア: なし（スタンドアロンアプリケーション）

## プロジェクト構成

```
SSky/
├── SSky.py                 # メインエントリーポイント
├── SConstruct              # SCons ビルドスクリプト
├── make-requirements.bat   # 依存関係生成スクリプト
├── requirements.txt        # 依存ライブラリリスト
├── config/                 # 設定関連
│   ├── app_config.json     # アプリケーション設定ファイル
│   ├── app_config.py       # 設定管理クラス
│   └── logging_config.py   # ロギング設定
├── core/                   # コア機能
│   ├── client.py           # Blueskyクライアントラッパー
│   ├── data_store.py       # データ保存
│   └── auth/               # 認証関連
│       └── auth_manager.py # 認証管理
├── gui/                    # GUI関連
│   ├── app.py              # アプリケーションクラス
│   ├── main_frame.py       # メインウィンドウ
│   ├── timeline_view.py    # タイムラインビュー
│   ├── dialogs/            # 各種ダイアログ
│   └── handlers/           # イベントハンドラ
├── utils/                  # ユーティリティ
│   ├── crypto.py           # 暗号化ユーティリティ
│   ├── file_utils.py       # ファイル操作ユーティリティ
│   ├── time_format.py      # 時間フォーマットユーティリティ
│   └── url_utils.py        # URL操作ユーティリティ
├── manual/                 # マニュアル
│   └── readme.md           # ユーザー向けマニュアル
└── tests/                  # テスト
    ├── run_tests.py        # テスト実行スクリプト
    └── test_*.py           # 各種テスト
```

## 必要なライブラリ

主な依存ライブラリ:

- atproto==0.0.61 - Bluesky API クライアント
- pywin32==310 - Windows API アクセス
- wxPython - GUI フレームワーク
- SCons - ビルドツール
- PyInstaller - パッケージングツール

## 開発環境のセットアップ

1. Python 3.13.2をインストール
2. 必要なライブラリをインストール

```cmd
pip install -r requirements.txt
pip install wxPython
pip install scons
pip install pyinstaller
pip install pipreqs
```

3. (オプション) pre-commitのセットアップ
   - プロジェクトには.pre-commit-configファイルが用意されています
   - コード品質を維持するために、pre-commitを導入することをお勧めします

```cmd
pip install pre-commit
pre-commit install
```

## 開発方法

### アプリケーションの実行（開発モード）

```cmd
python SSky.py
```

### 依存関係の更新

プロジェクトの依存関係を更新するには、以下のコマンドを実行します：

```cmd
make-requirements.bat
```

または

```cmd
pipreqs .\ --encoding=utf-8 --savepath requirements.txt --force
```

### テストの実行

```cmd
python tests\run_tests.py
```

## ビルド方法

### 実行可能ファイルのビルド

Pyinstaller を使用して実行可能なexeファイルを作成します。

```cmd
pyinstaller --name SSky --noconsole --onedir --noupx --clean --noconfirm --log-level=INFO SSky.py
```

ビルドされたexeファイルが Windows Defender でウイルス検知される場合は、ソースコードからビルドした Pyinstaller を利用してください。

```cmd
pip uninstall -y pyinstaller
pip install wheel
git clone https://github.com/pyinstaller/pyinstaller.git # PyInstallerのソースをクローン
cd pyinstaller\bootloader
python .\waf distclean all
cd ..
pip install .
```

### パッケージング

SCons を使用してzipファイルにパッケージングします。バージョン番号を指定する必要があります：

```
scons --release=1.0.0
```

このコマンドは以下の処理を行います：

1. PyInstallerを使用してSSky.pyをビルド
2. 必要なファイル（マニュアル、changelog.mdなど）をパッケージディレクトリにコピー
3. zipファイルを作成

ビルド結果は以下の場所に生成されます：

- パッケージディレクトリ: `build/SSky-{version}/`
- zipファイル: `release/SSky-{version}.zip`

## アーキテクチャ

SSkyは以下のコンポーネントで構成されています：

- **コア (core/)**: Bluesky APIとの通信、認証管理、データ保存などの基本機能を提供
- **GUI (gui/)**: ユーザーインターフェース（メインウィンドウ、タイムラインビュー、各種ダイアログなど）
- **ユーティリティ (utils/)**: 暗号化、ファイル操作、時間フォーマット、URL操作などの共通機能
- **設定 (config/)**: アプリケーション設定の管理、ロギング設定

## 主要クラス

- **SSkyApp**: アプリケーションのメインクラス
- **MainFrame**: メインウィンドウ
- **TimelineView**: タイムラインの表示と操作
- **BlueskyClient**: Bluesky APIのラッパー
- **AuthManager**: 認証情報の管理
- **AppConfig**: アプリケーション設定の管理

## ライセンス

このプロジェクトのライセンスについては、LICENSEファイルを参照してください。

## 連絡先・バグ報告

バグや機能要望などがある場合は、GitHubリポジトリにissueを立ててください。
プルリクエストも歓迎です。その際はdevelopブランチにプルリクエストしてください。
https://github.com/kenny7968/SSky
