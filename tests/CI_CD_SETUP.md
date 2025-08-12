# SSky CI/CD テスト設定ガイド

## GitHub Actions 設定例

### 基本的なワークフロー（.github/workflows/test.yml）

```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  PYTHON_VERSION: '3.13'
  PYTEST_ARGS: '-v --tb=short --strict-markers'

jobs:
  # ステージ1: 高速な単体テスト
  unit-tests:
    name: Unit Tests
    runs-on: windows-latest
    timeout-minutes: 10
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-mock pytest-timeout
    
    - name: Run Core Unit Tests
      run: |
        pytest tests/unit/core \
          -m "not gui and not slow" \
          --cov=core \
          --cov-report=xml \
          --cov-report=term-missing \
          --cov-fail-under=90 \
          ${{ env.PYTEST_ARGS }}
    
    - name: Run Utils Unit Tests
      run: |
        pytest tests/unit/utils \
          -m "not gui" \
          --cov=utils \
          --cov-append \
          --cov-report=xml \
          --cov-fail-under=85 \
          ${{ env.PYTEST_ARGS }}
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: unit-coverage
        fail_ci_if_error: false

  # ステージ2: 統合テスト（単体テスト成功後のみ）
  integration-tests:
    name: Integration Tests
    needs: unit-tests
    runs-on: windows-latest
    timeout-minutes: 15
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-timeout
    
    - name: Run Integration Tests
      run: |
        pytest tests/integration \
          -m "not gui and not e2e" \
          --maxfail=5 \
          --timeout=60 \
          ${{ env.PYTEST_ARGS }}

  # ステージ3: 静的解析
  static-analysis:
    name: Static Analysis
    runs-on: windows-latest
    timeout-minutes: 10
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install analysis tools
      run: |
        pip install flake8 mypy black isort bandit
    
    - name: Run flake8
      run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
      continue-on-error: true
    
    - name: Run black check
      run: black --check .
      continue-on-error: true
    
    - name: Run isort check
      run: isort --check-only .
      continue-on-error: true
    
    - name: Run security check with bandit
      run: bandit -r core/ -f json -o bandit-report.json
      continue-on-error: true

  # オプション: Nightly ビルド用の完全テスト
  full-test-suite:
    name: Full Test Suite (Nightly)
    if: github.event_name == 'schedule'
    runs-on: windows-latest
    timeout-minutes: 30
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install all dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run all tests
      run: |
        pytest tests/ \
          -m "not gui" \
          --cov=. \
          --cov-report=html \
          --html=report.html \
          --self-contained-html
    
    - name: Upload test report
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-report
        path: |
          report.html
          htmlcov/
```

## GitLab CI 設定例（.gitlab-ci.yml）

```yaml
stages:
  - test
  - coverage
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  PYTEST_ARGS: "-v --tb=short"

cache:
  paths:
    - .cache/pip
    - venv/

before_script:
  - python -m venv venv
  - venv\Scripts\activate
  - pip install --upgrade pip
  - pip install -r requirements.txt
  - pip install pytest pytest-cov pytest-mock

unit-tests:
  stage: test
  script:
    - venv\Scripts\activate
    - pytest tests/unit/core -m "not gui" --cov=core --cov-report=term
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
  only:
    - branches
  except:
    - tags

integration-tests:
  stage: test
  script:
    - venv\Scripts\activate
    - pytest tests/integration -m "not gui and not e2e"
  dependencies:
    - unit-tests
  only:
    - develop
    - main
```

## Azure Pipelines 設定例（azure-pipelines.yml）

```yaml
trigger:
  branches:
    include:
    - main
    - develop
  paths:
    exclude:
    - docs/*
    - '*.md'

pool:
  vmImage: 'windows-latest'

variables:
  pythonVersion: '3.13'
  pipCacheDir: $(Pipeline.Workspace)/.pip

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '$(pythonVersion)'
  displayName: 'Use Python $(pythonVersion)'

- task: Cache@2
  inputs:
    key: 'pip | "$(Agent.OS)" | requirements.txt'
    path: $(pipCacheDir)
  displayName: Cache pip packages

- script: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install pytest pytest-azurepipelines pytest-cov
  displayName: 'Install dependencies'

- script: |
    pytest tests/unit/core -m "not gui" --cov=core --cov-report=xml --cov-report=html
  displayName: 'Run unit tests'

- task: PublishCodeCoverageResults@1
  inputs:
    codeCoverageTool: 'Cobertura'
    summaryFileLocation: '$(System.DefaultWorkingDirectory)/coverage.xml'
    reportDirectory: '$(System.DefaultWorkingDirectory)/htmlcov'
  displayName: 'Publish coverage results'

- task: PublishTestResults@2
  inputs:
    testResultsFormat: 'JUnit'
    testResultsFiles: '**/test-*.xml'
  displayName: 'Publish test results'
```

## Jenkins Pipeline 設定例（Jenkinsfile）

```groovy
pipeline {
    agent {
        label 'windows'
    }
    
    environment {
        PYTHON_VERSION = '3.13'
        VENV_DIR = "${WORKSPACE}/venv"
    }
    
    stages {
        stage('Setup') {
            steps {
                bat '''
                    python -m venv %VENV_DIR%
                    call %VENV_DIR%\\Scripts\\activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest pytest-cov pytest-html
                '''
            }
        }
        
        stage('Unit Tests') {
            steps {
                bat '''
                    call %VENV_DIR%\\Scripts\\activate
                    pytest tests/unit/core -m "not gui" ^
                        --cov=core ^
                        --cov-report=xml ^
                        --junitxml=test-results/junit.xml ^
                        --html=test-results/report.html
                '''
            }
            post {
                always {
                    junit 'test-results/junit.xml'
                    publishHTML([
                        reportDir: 'test-results',
                        reportFiles: 'report.html',
                        reportName: 'Test Report'
                    ])
                    cobertura coberturaReportFile: 'coverage.xml'
                }
            }
        }
        
        stage('Integration Tests') {
            when {
                branch 'develop'
            }
            steps {
                bat '''
                    call %VENV_DIR%\\Scripts\\activate
                    pytest tests/integration -m "not gui"
                '''
            }
        }
    }
    
    post {
        failure {
            emailext (
                subject: "Build Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "The build failed. Check console output at ${env.BUILD_URL}",
                to: 'dev-team@example.com'
            )
        }
    }
}
```

## ローカル開発用 Makefile

```makefile
.PHONY: test test-unit test-integration test-gui test-all coverage clean

# Python環境
PYTHON := python
VENV := venv
PYTEST := $(VENV)/Scripts/pytest
PIP := $(VENV)/Scripts/pip

# テスト設定
PYTEST_ARGS := -v --tb=short --strict-markers
COV_ARGS := --cov=core --cov=utils --cov=gui --cov=config

# 仮想環境のセットアップ
$(VENV):
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

# 単体テストのみ（高速）
test: $(VENV)
	$(PYTEST) tests/unit -m "not gui and not slow" $(PYTEST_ARGS)

# 単体テスト（詳細）
test-unit: $(VENV)
	$(PYTEST) tests/unit $(PYTEST_ARGS) $(COV_ARGS)

# 統合テスト
test-integration: $(VENV)
	$(PYTEST) tests/integration -m "not gui" $(PYTEST_ARGS)

# GUIテスト（要ディスプレイ）
test-gui: $(VENV)
	$(PYTEST) tests/gui $(PYTEST_ARGS)

# 全テスト実行
test-all: $(VENV)
	$(PYTEST) tests/ $(PYTEST_ARGS) $(COV_ARGS) --cov-report=html

# カバレッジレポート生成
coverage: test-all
	@echo "Coverage report generated in htmlcov/index.html"
	@start htmlcov/index.html

# クリーンアップ
clean:
	rmdir /s /q $(VENV) 2>nul || true
	rmdir /s /q .pytest_cache 2>nul || true
	rmdir /s /q htmlcov 2>nul || true
	del /q .coverage 2>nul || true
	del /q coverage.xml 2>nul || true
```

## Docker を使用したテスト環境

```dockerfile
# Dockerfile.test
FROM python:3.13-slim-windows

WORKDIR /app

# 依存関係のインストール
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# アプリケーションコードのコピー
COPY . .

# テスト実行
CMD ["pytest", "tests/unit", "-m", "not gui", "--cov=.", "--cov-report=term-missing"]
```

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  test:
    build:
      context: .
      dockerfile: Dockerfile.test
    volumes:
      - .:/app
      - test-cache:/app/.pytest_cache
    environment:
      - PYTHONDONTWRITEBYTECODE=1
      - PYTEST_ARGS=-v --tb=short

volumes:
  test-cache:
```

## 実行例

### ローカル開発
```bash
# 変更したファイルのテストのみ
pytest tests/unit --lf

# 特定のテストをデバッグ
pytest -xvs tests/unit/core/auth/test_credential_manager.py::test_specific

# カバレッジ付き実行
pytest --cov=core --cov-report=html
```

### CI環境
```bash
# 必須テストのみ（高速）
pytest tests/unit -m "not gui and not slow" --maxfail=1

# プルリクエスト用
pytest tests/unit tests/integration -m "not gui" --cov-fail-under=85
```

### リリース前
```bash
# 完全テストスイート
pytest tests/ --slow --cov=. --cov-report=html
```

## トラブルシューティング

### よくある問題と解決策

1. **Windows環境でのパス問題**
   ```yaml
   # 正しい
   - run: pytest tests\unit
   # または
   - run: pytest tests/unit
   ```

2. **タイムアウト設定**
   ```yaml
   - run: pytest --timeout=60 --timeout-method=thread
   ```

3. **並列実行**
   ```yaml
   - run: pytest -n auto  # pytest-xdist が必要
   ```

4. **メモリ不足**
   ```yaml
   - run: pytest --maxfail=5  # 早期終了
   ```

---

最終更新: 2025-08-12
このドキュメントは継続的に更新されます。