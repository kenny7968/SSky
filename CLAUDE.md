# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```cmd
python SSky.py
```

### Testing
```cmd
python tests\run_tests.py
```

### Building and Packaging
```cmd
# Build executable with PyInstaller
pyinstaller --name SSky --noconsole --onedir --noupx --clean --noconfirm --log-level=INFO SSky.py

# Package with SCons (specify version)
scons --release=1.0.0

# Update dependencies
make-requirements.bat
# or
pipreqs .\ --encoding=utf-8 --savepath requirements.txt --force
```

### Pre-commit Setup (Optional)
```cmd
pip install pre-commit
pre-commit install
```

## Architecture Overview

SSky is a screen reader-optimized Windows Bluesky client built with Python 3.13 and wxPython. The application uses a modular architecture with clear separation between core functionality, GUI components, and utilities.

### Core Architecture Components

- **Entry Point**: `SSky.py` - Main application launcher
- **Core Layer** (`core/`): Business logic and API communication
  - `client/api_client.py` - BlueskyApiClient wraps atproto library for all Bluesky operations
  - `client/facade.py` - BlueskyClient facade providing higher-level operations
  - `auth/credential_manager.py` - Authentication and credential management with Windows DPAPI encryption
  - `data_store.py` - SQLite database operations for persistent data
  - `error_handler.py` - Centralized error handling
  - `events.py` - PubSub event definitions for authentication and other events

- **GUI Layer** (`gui/`): User interface components
  - `app.py` - SSkyApp main application class
  - `main_frame.py` - MainFrame window with menu system and layout
  - `timeline/timeline_view.py` - TimelineView with auto-refresh and TimelineListCtrl for post display
  - `dialogs/` - Various dialog classes (login, post creation, user lists, etc.)
  - `handlers/` - Event handlers for authentication and post operations

- **Configuration** (`config/`): Application settings and configuration
  - `app_config.py` - Application configuration management
  - `settings_manager.py` - User settings with observer pattern
  - `logging_config.py` - Centralized logging setup

- **Utilities** (`utils/`): Common functionality
  - `auth_decorators.py` - Authentication requirement decorators
  - `crypto.py` - Windows DPAPI encryption utilities
  - `time_format.py` - Time formatting (relative times, JST conversion)
  - `file_utils.py` - File operations
  - `url_utils.py` - URL detection and handling

### Key Architectural Patterns

1. **PubSub Event System**: Authentication events use PubSub pattern for loose coupling
2. **Observer Pattern**: Settings changes notify registered observers
3. **Facade Pattern**: BlueskyClient provides simplified interface over API client
4. **Decorator Pattern**: `@require_authentication` decorates methods requiring login
5. **Singleton Pattern**: Settings and credential managers use singleton instances

### Authentication Flow

1. Credentials stored encrypted with Windows DPAPI in SQLite database
2. Session management handles automatic login attempts and token refresh
3. PubSub events notify UI components of authentication state changes
4. Authentication decorators protect methods requiring login

### Timeline and Data Management

- Timeline auto-refreshes based on user settings
- Posts stored temporarily for offline access
- Data persistence through SQLite with structured schema
- Efficient list control for large timeline data

### Error Handling Strategy

- Centralized error handling through `core/error_handler.py`
- Network errors, authentication failures, and API errors handled gracefully
- User-friendly error messages with appropriate logging
- Graceful degradation when services unavailable

## Development Guidelines

### Code Organization
- Follow the existing modular structure
- Use type hints where appropriate
- Japanese comments are acceptable as this is a Japanese-focused application
- Error messages should be user-friendly in Japanese

### Dependencies
- Main dependencies: `atproto==0.0.61`, `pywin32==310`, `PyPubSub==4.0.3`
- wxPython must be installed separately: `pip install wxPython`
- Windows-specific DPAPI encryption requires pywin32

### Testing
- Tests located in `tests/` directory
- Run all tests with `python tests\run_tests.py`
- Individual test files can be run directly

### Building
- Development builds use PyInstaller directly
- Production packages use SCons build system
- Version numbers specified via `--release` parameter to SCons