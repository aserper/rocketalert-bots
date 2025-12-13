# RocketAlert Bots

A bot service for monitoring Rocket Alerts and posting them to Telegram and Mastodon.

## Overview

This application listens to a RocketAlert API server for incoming alerts and automatically posts them to configured social media platforms (Telegram and Mastodon). The bot handles message formatting, character limits per platform, and error recovery.

## Project Structure

### Core Files

- **main.py** - Application entry point. Connects to RocketAlert API and processes events in a loop
- **rocket_alert_api.py** - API client for connecting to RocketAlert server (SSE streaming)
- **message_manager.py** - Orchestrates alert processing and bot coordination
- **message_builder.py** - Formats alert data into human-readable messages
- **telegram_bot.py** - Sends messages to Telegram (4096 char limit per message)
- **mastodon_bot.py** - Sends messages to Mastodon (500 char limit per message)

### Configuration & Data

- **requirements.txt** - Python dependencies (auto-generated, edit requirements.in instead)
- **requirements.in** - Source file for dependency management (used with pip-compile)
- **Dockerfile** - Container image definition (Alpine Linux + Python)
- **pytest.ini** - Test configuration
- **.coveragerc** - Code coverage settings (70% minimum threshold)
- **polygons.json** - Geographic polygon data for map generation (disabled in current version)

## Environment Variables

### Required

```bash
# Rocket Alert API Configuration
RA_BASEURL=https://rocketalert.live/api          # Base URL for Rocket Alert API
CUSTOM_HEADER_KEY=X-Custom-Header                # Custom header name for API auth
CUSTOM_HEADER_VALUE=your-secret-value            # Custom header value for API auth

# Telegram Configuration
TELEGRAM_API_ID=123456789                        # From https://my.telegram.org/apps
TELEGRAM_API_HASH=0123456789abcdef               # From https://my.telegram.org/apps

# Mastodon Configuration
MASTO_BASEURL=https://mastodon.social            # Mastodon instance URL
MASTO_ACCESS_TOKEN=your-access-token             # From Mastodon instance settings
```

### Optional

```bash
COMMIT_SHA=abc123def456                          # Git commit SHA (set by Docker build)
```

## Configuration Details

### Rocket Alert API

- **Endpoint:** `{RA_BASEURL}/real-time`
- **Method:** GET with SSE (Server-Sent Events)
- **Timeout:** 120 seconds
- **Headers:** Custom header for authentication + Firefox User-Agent

### Telegram

- **Account Type:** Bot channel (@RocketAlert)
- **Character Limit:** 4096 characters per message
- **Truncation:** Messages exceeding limit are split into multiple parts
- **Session:** Stored locally in `/session/session_name` (created on first auth)
- **Implementation:** Uses `telethon.sync` for synchronous operation

### Mastodon

- **Instance:** Configurable (e.g., mastodon.social)
- **Character Limit:** 500 characters per message
- **Timeout:** 30 seconds per request
- **Visibility:** Public (default)

## Testing

### Quick Start

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_telegram_bot.py -v
```

### Test Overview

- **Total Tests:** 59 (44 unit + 7 integration + 8 utility)
- **Coverage:** 71.67% (exceeds 70% minimum threshold)
- **Framework:** pytest with asyncio support

### Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and test data
├── unit/
│   ├── test_message_builder.py   # Message formatting tests
│   ├── test_telegram_bot.py      # Telegram bot tests
│   ├── test_mastodon_bot.py      # Mastodon bot tests
│   ├── test_message_manager.py   # Event orchestration tests
│   └── test_rocket_alert_api.py  # API client tests
└── integration/
    └── test_end_to_end.py        # Full workflow tests
```

### Test Components

**Unit Tests (44 tests):**
- Message builder and formatting (13 tests)
- Telegram bot operations (10 tests)
- Mastodon bot operations (12 tests)
- Message manager coordination (8 tests)
- API client functionality (9 tests)

**Integration Tests (7 tests):**
- Full event processing pipeline
- Multiple alert batching
- Different alert types (Rocket, UAV, Red Alert)
- Error recovery and fallback mechanisms
- Message truncation for long alert lists
- Hebrew/English text handling
- Timestamp inclusion validation

### Coverage Requirements

- **Minimum Threshold:** 70%
- **Enforcement:** CI/CD fails if coverage drops below threshold
- **Excluded:** Tests, __pycache__, venv directories
- **Report:** HTML coverage available in `htmlcov/` directory

For detailed testing information, see [TESTING.md](./TESTING.md).

## Docker

### Building

```bash
# Build locally
docker build --build-arg COMMIT_SHA=$(git rev-parse HEAD) -t rocketalert-bots:latest .

# The build argument captures the current git commit for version tracking
```

### Running

```bash
# Docker Hub
docker run -e RA_BASEURL="https://..." \
           -e CUSTOM_HEADER_KEY="..." \
           -e CUSTOM_HEADER_VALUE="..." \
           -e TELEGRAM_API_ID="..." \
           -e TELEGRAM_API_HASH="..." \
           -e MASTO_BASEURL="..." \
           -e MASTO_ACCESS_TOKEN="..." \
           amitserper/rocketalert-mastodon

# GitHub Container Registry (private)
docker run -e RA_BASEURL="https://..." \
           ... (same environment variables)
           ghcr.io/aserper/rocketalert-bots:latest
```

### Logging

The container outputs timestamps and detailed logs to stdout:
```
2025-12-13 01:12:45 - Starting version: abc123def456 - Connecting to server...
2025-12-13 01:12:57 - Received server event: {...}
2025-12-13 01:12:57 - Processing event...
2025-12-13 01:12:57 - Building alert message...
2025-12-13 01:12:57 - Posting: Message 1/1:
2025-12-13 01:12:57 - To Telegram...done.
2025-12-13 01:12:57 - To Mastodon...done.
```

### Debugging

Send SIGUSR1 signal to dump Python traceback:
```bash
docker exec <container-id> kill -USR1 1
# Traceback will be printed to container logs
```

## Local Development

### Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or use pip-compile for reproducible installs
pip-compile requirements.in
pip install -r requirements.txt
```

### Running Locally

```bash
# Set environment variables
export RA_BASEURL="https://..."
export CUSTOM_HEADER_KEY="..."
export CUSTOM_HEADER_VALUE="..."
export TELEGRAM_API_ID="..."
export TELEGRAM_API_HASH="..."
export MASTO_BASEURL="..."
export MASTO_ACCESS_TOKEN="..."

# Run
python main.py
```

## Message Formatting

### Alert Components

- **Header:** "Rocket alert {timestamp}:"
- **Locations:** List of affected areas with coordinates
- **Format by Area:**
  - English name + area (if available): `Patish (Western Negev)`
  - Hebrew fallback: `פטיש`
  - Missing name: `Unknown`

### Platform-Specific Handling

**Telegram (4096 char limit):**
- Footer link added: `[RocketAlert.live](https://RocketAlert.live)`
- Messages split on line boundaries if needed
- No links preview in messages

**Mastodon (500 char limit):**
- Stricter truncation
- Each alert posted separately if combined exceeds limit
- Text only (no media)

## Dependencies

### Core Libraries

- **requests** - HTTP client for API calls
- **telethon** - Telegram Bot API client (v1.36.0)
- **mastodon-py** - Mastodon API client (v1.8.1)

### Testing Libraries

- **pytest** - Test framework
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mocking utilities
- **pytest-asyncio** - Async test support
- **responses** - HTTP request mocking

See `requirements.txt` for full dependency tree with versions.

## CI/CD

GitHub Actions workflow (`.github/workflows/Masto-rocketalert.yml`):

### Test Job
- Runs on every push and PR
- Python 3.10 environment
- Installs dependencies and runs full test suite
- Enforces 70% code coverage threshold
- Blocks Docker build if tests fail

### Build Job
- Only runs on pushes to main branch
- Depends on test job passing
- Builds Docker image with commit SHA
- Pushes to Docker Hub (public: `amitserper/rocketalert-mastodon`)
- Pushes to GHCR (initially public, can be made private)

### Making GHCR Image Private

After first push to GHCR:
1. Go to https://github.com/aserper?tab=packages
2. Click "rocketalert-bots" package
3. Click "Package settings"
4. Change visibility to "Private"
5. Set access to your account only

## Known Issues & Troubleshooting

### Bot Hangs During Message Posting

**Symptom:** Logs show "To Telegram..." but never progress to "done."

**Root Cause:** Event loop deadlock when using `run_until_complete()` on already-running loop

**Fix:** Use `telethon.sync` module for synchronous operation (see PR #34)

**Current Status:** ✅ Fixed in `telegram_bot.py:2` (imports from `telethon.sync`)

### Telegram Session Issues

**Problem:** Bot requires interactive authentication on first run

**Solution:** Create the `/session` directory beforehand or handle auth flow in deployment environment

### Mastodon API Timeouts

**Problem:** 30-second timeout might be insufficient for slow instances

**Workaround:** Increase timeout in `mastodon_bot.py.__init__()` if needed

### Binary Files in Git

**Status:** ✅ Resolved

Previously tracked `.pyc` files have been removed from git. `.gitignore` prevents future tracking:
- `__pycache__/` - All compiled Python bytecode
- `.pytest_cache/` - Test cache
- `venv/`, `.venv/` - Virtual environments

## Git Commit Configuration

Configure git identity for commits:

```bash
# Set username to GitHub handle
git config --global user.name "aserper"

# Set email to GitHub noreply email
git config --global user.email "aserper@users.noreply.github.com"
```

## Contributing

1. Create a feature branch: `git checkout -b feature/description`
2. Make changes and test locally
3. Run full test suite: `pytest tests/ -v`
4. Commit with clear messages (no "claude" mentions)
5. Push branch and create PR
6. Wait for CI/CD to pass (tests required)
7. Request review from team members

## Useful Commands

```bash
# Update dependencies
pip-compile requirements.in

# Check test coverage
pytest tests/ --cov=. --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=. --cov-report=html
# View at: htmlcov/index.html

# Run tests in verbose mode
pytest tests/ -v

# Run tests with output capture disabled (see prints)
pytest tests/ -v -s

# View Docker Hub image
docker pull amitserper/rocketalert-mastodon

# Check image size
docker images amitserper/rocketalert-mastodon
```

## References

- [TESTING.md](./TESTING.md) - Comprehensive testing guide
- [RocketAlert API](https://rocketalert.live/) - Alert service
- [Telethon Docs](https://docs.telethon.dev/) - Telegram Bot API client
- [Mastodon.py Docs](https://mastodonpy.readthedocs.io/) - Mastodon API client
