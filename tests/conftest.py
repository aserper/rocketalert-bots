import pytest
import json
import os
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from pathlib import Path


@pytest.fixture
def sample_alert():
    """Single alert from test_alerts.json"""
    return {
        "name": "נירים",
        "englishName": "Nirim",
        "lat": 31.3357,
        "lon": 34.3941,
        "taCityId": 171,
        "countdownSec": 15,
        "areaNameHe": "עוטף עזה",
        "areaNameEn": "Gaza Envelope",
        "timeStamp": "2023-12-04 16:59:09"
    }


@pytest.fixture
def alert_hebrew_only():
    """Alert with only Hebrew names (no English names)"""
    return {
        "name": "נירים",
        "englishName": None,
        "lat": 31.3357,
        "lon": 34.3941,
        "taCityId": 171,
        "countdownSec": 15,
        "areaNameHe": "עוטף עזה",
        "areaNameEn": None,
        "timeStamp": "2023-12-04 16:59:09"
    }


@pytest.fixture
def alert_missing_area():
    """Alert with missing area names"""
    return {
        "name": "נירים",
        "englishName": "Nirim",
        "lat": 31.3357,
        "lon": 34.3941,
        "taCityId": 171,
        "countdownSec": 15,
        "areaNameHe": None,
        "areaNameEn": None,
        "timeStamp": "2023-12-04 16:59:09"
    }


@pytest.fixture
def sample_event_data(sample_alert):
    """Complete event data structure"""
    return {
        "alertTypeId": 1,
        "alerts": [sample_alert]
    }


@pytest.fixture
def multi_alert_event():
    """Event with multiple alerts from test_alerts.json"""
    alerts_file = Path(__file__).parent.parent / "test_alerts.json"
    with open(alerts_file) as f:
        alerts = json.load(f)
    return {
        "alertTypeId": 1,
        "alerts": alerts[:5]  # First 5 alerts
    }


@pytest.fixture
def test_alerts_data():
    """Full test_alerts.json data"""
    alerts_file = Path(__file__).parent.parent / "test_alerts.json"
    with open(alerts_file) as f:
        return json.load(f)


@pytest.fixture
def mock_telegram_client():
    """Mocked TelegramClient"""
    client = MagicMock()
    client.start = Mock()
    client.send_message = AsyncMock()

    # Mock event loop
    loop = MagicMock()
    loop.run_until_complete = Mock(side_effect=lambda coro: None)
    client.loop = loop

    return client


@pytest.fixture
def mock_mastodon_client():
    """Mocked Mastodon client"""
    client = MagicMock()
    client.status_post = Mock()
    return client


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables"""
    env_vars = {
        "RA_BASEURL": "https://test-api.example.com",
        "CUSTOM_HEADER_VALUE": "test-value",
        "CUSTOM_HEADER_KEY": "X-Test-Header",
        "MAPBOX_TOKEN": "test-mapbox-token",
        "TELEGRAM_API_ID": "12345",
        "TELEGRAM_API_HASH": "test-hash",
        "MASTO_BASEURL": "https://test-mastodon.social",
        "MASTO_ACCESS_TOKEN": "test-token"
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


@pytest.fixture
def message_builder(mock_env_vars):
    """AlertMessageBuilder instance with mocked environment"""
    from message_builder import AlertMessageBuilder
    return AlertMessageBuilder()


@pytest.fixture
def long_message():
    """Message exceeding Telegram limit (4096 chars)"""
    return "Location\n" * 300  # ~3000 chars


@pytest.fixture
def very_long_message():
    """Message far exceeding both platform limits"""
    return "Very long location name\n" * 500  # ~12000 chars


@pytest.fixture
def keep_alive_event():
    """Keep-alive event that should be filtered"""
    return {
        "alertTypeId": 0,
        "alerts": [{
            "name": "KEEP_ALIVE",
            "timeStamp": "2023-12-04 16:59:09"
        }]
    }
