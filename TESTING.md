# Testing Guide for RocketAlert Bots

This document describes the testing infrastructure and how to run tests for the RocketAlert Bots project.

## Overview

The test suite provides comprehensive coverage of the codebase with both unit and integration tests. All tests are automated and run in CI/CD on every pull request and push to main.

**Current Coverage: 71.67%** (exceeds 70% minimum threshold)

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and test data
├── unit/                          # Unit tests for individual components
│   ├── test_message_builder.py   # AlertMessageBuilder tests
│   ├── test_telegram_bot.py      # TelegramBot tests
│   ├── test_mastodon_bot.py      # MastodonBot tests
│   ├── test_message_manager.py   # MessageManager tests
│   └── test_rocket_alert_api.py  # RocketAlertAPI tests
└── integration/                   # Integration tests
    └── test_end_to_end.py        # Full flow integration tests
```

## Running Tests

### Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have Python 3.10+ installed

### Running All Tests

```bash
pytest
```

### Running with Coverage

```bash
pytest --cov=. --cov-report=html --cov-report=term-missing
```

View HTML coverage report:
```bash
# Open in browser
xdg-open htmlcov/index.html  # Linux
open htmlcov/index.html       # macOS
```

### Running Specific Test Suites

**Unit tests only:**
```bash
pytest tests/unit/
```

**Integration tests only:**
```bash
pytest tests/integration/
```

**Specific test file:**
```bash
pytest tests/unit/test_message_builder.py -v
```

**Specific test:**
```bash
pytest tests/unit/test_message_builder.py::TestAlertMessageBuilder::test_buildAlert_with_both_english_names -v
```

### Running Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

## Test Configuration

### pytest.ini

Key configuration:
- Test discovery: `tests/` directory
- Asyncio mode: auto
- Test markers: `unit`, `integration`, `slow`, `requires_network`
- Verbose output with colors

### .coveragerc

Coverage configuration:
- Source: all project files
- Omit: tests, cache, venv
- Minimum coverage: 70% (enforced in CI)
- HTML reports in `htmlcov/`

## Test Fixtures

Common fixtures defined in `conftest.py`:

- `sample_alert`: Single alert from test data
- `sample_event_data`: Complete event structure
- `multi_alert_event`: Event with multiple alerts
- `mock_telegram_client`: Mocked Telegram client
- `mock_mastodon_client`: Mocked Mastodon client
- `mock_env_vars`: Mock environment variables
- `message_builder`: AlertMessageBuilder instance

## Component Coverage

| Component | Coverage | Focus |
|-----------|----------|-------|
| mastodon_bot.py | 100.00% | Message posting, truncation, timeout |
| rocket_alert_api.py | 100.00% | API client, headers, streaming |
| message_manager.py | 97.56% | Event processing, bot coordination |
| telegram_bot.py | 80.56% | Message posting, async handling |
| message_builder.py | 79.73% | Message formatting, alert types |
| main.py | 0.00% | Event loop (difficult to test) |

## What's Tested

### Unit Tests

**AlertMessageBuilder:**
- Alert formatting with Hebrew/English names
- Message text construction for different alert types
- Polygon overlay and marker generation
- Message truncation and splitting

**TelegramBot:**
- Message sending (under/over 4096 char limit)
- Message truncation logic
- List handling
- Error handling

**MastodonBot:**
- Message sending (under/over 500 char limit)
- Message truncation logic
- 30-second timeout configuration
- Error handling

**MessageManager:**
- Single and multiple alert processing
- Telegram footer addition
- Bot error handling
- Alert type routing

**RocketAlertAPI:**
- Environment variable configuration
- Header construction (custom headers, user-agent)
- SSE connection setup
- Timeout and streaming parameters

### Integration Tests

- Full event processing flow (API → message → bots)
- Different alert types (Rocket, UAV, Red)
- Error recovery from bot failures
- Multi-alert batch processing
- Hebrew/English text handling
- Timestamp inclusion

## CI/CD Integration

Tests run automatically on:
- Every push to `main` branch
- Every pull request to `main` branch

### GitHub Actions Workflow

`.github/workflows/Masto-rocketalert.yml`:

1. **Test Job** (runs first):
   - Sets up Python 3.10
   - Installs dependencies
   - Runs tests with coverage
   - Enforces 70% coverage minimum
   - Uploads coverage to Codecov (optional)

2. **Build Job** (runs after tests pass):
   - Only on main branch pushes
   - Builds and pushes Docker image
   - **Only runs if tests pass**

### Test Failure Handling

- If tests fail, the build is blocked
- Coverage below 70% fails the build
- Pull requests cannot merge until tests pass

## Writing New Tests

### Test Organization

1. Unit tests go in `tests/unit/`
2. Integration tests go in `tests/integration/`
3. Use descriptive test names: `test_<action>_<expected_result>`
4. Group related tests in classes

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
class TestMyComponent:
    """Tests for MyComponent class"""

    def test_something_specific(self, mock_env_vars):
        """Test description"""
        # Arrange
        component = MyComponent()

        # Act
        result = component.do_something()

        # Assert
        assert result == expected_value
```

### Best Practices

1. **Mock external dependencies**: Never make real API calls
2. **Use fixtures**: Reuse common test data from `conftest.py`
3. **Test edge cases**: Empty inputs, None values, boundary conditions
4. **Clear assertions**: One assertion per concept
5. **Descriptive names**: Test names should explain what's being tested
6. **Fast execution**: All tests should run in < 30 seconds

### Adding Fixtures

Add new fixtures to `tests/conftest.py`:

```python
@pytest.fixture
def my_fixture():
    """Description of what this fixture provides"""
    return {"data": "value"}
```

## Troubleshooting

### Tests Fail Locally

1. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Check Python version (3.10+ required):
   ```bash
   python --version
   ```

3. Clear pytest cache:
   ```bash
   pytest --cache-clear
   ```

### Coverage Too Low

1. Run coverage report to see missing lines:
   ```bash
   pytest --cov=. --cov-report=term-missing
   ```

2. Add tests for uncovered code paths

3. Focus on critical business logic first

### Import Errors

Ensure project root is in PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

## Maintenance

### Updating Test Dependencies

1. Edit `requirements.in`
2. Regenerate requirements:
   ```bash
   pip-compile requirements.in
   ```
3. Install updated dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Test Dependencies

- `pytest==8.4.1`: Test framework
- `pytest-asyncio==0.24.0`: Async test support
- `pytest-mock==3.14.0`: Enhanced mocking
- `pytest-cov==6.0.0`: Coverage reporting
- `responses==0.25.0`: HTTP mocking
- `coverage[toml]==7.6.9`: Coverage tool

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## Questions?

If you encounter issues with tests:
1. Check this documentation
2. Review existing tests for examples
3. Run tests with `-vv` flag for detailed output
4. Check CI logs for environment-specific issues
