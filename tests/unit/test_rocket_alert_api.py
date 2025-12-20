import pytest
from unittest.mock import Mock, patch
from rocket_alert_api import RocketAlertAPI


@pytest.mark.unit
class TestRocketAlertAPI:
    """Tests for RocketAlertAPI class"""

    def test_init_reads_environment_variables(self, mock_env_vars):
        """Test RocketAlertAPI initialization reads env vars correctly"""
        api = RocketAlertAPI()

        assert api.baseURL == "https://test-api.example.com"
        assert api.customHeaderValue == "test-value"
        assert api.customHeaderKey == "X-Test-Header"

    def test_init_creates_correct_headers(self, mock_env_vars):
        """Test RocketAlertAPI creates correct headers"""
        api = RocketAlertAPI()

        assert "X-Test-Header" in api.headers
        assert api.headers["X-Test-Header"] == "test-value"
        assert "user-agent" in api.headers
        assert "Chrome" in api.headers["user-agent"]

    @patch('rocket_alert_api.requests.get')
    def test_listenToServerEvents_correct_url(self, mock_get, mock_env_vars):
        """Test listenToServerEvents uses correct API URL"""
        api = RocketAlertAPI()
        api.listenToServerEvents()

        # Verify requests.get was called with correct URL
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://test-api.example.com/real-time"

    @patch('rocket_alert_api.requests.get')
    def test_listenToServerEvents_headers(self, mock_get, mock_env_vars):
        """Test listenToServerEvents includes custom headers and user-agent"""
        api = RocketAlertAPI()
        api.listenToServerEvents()

        # Verify headers were passed
        call_kwargs = mock_get.call_args[1]
        assert "headers" in call_kwargs
        headers = call_kwargs["headers"]

        assert "X-Test-Header" in headers
        assert headers["X-Test-Header"] == "test-value"
        assert "user-agent" in headers

    @patch('rocket_alert_api.requests.get')
    def test_listenToServerEvents_timeout(self, mock_get, mock_env_vars):
        """Test listenToServerEvents sets correct timeout"""
        api = RocketAlertAPI()
        api.listenToServerEvents()

        # Verify timeout parameter
        call_kwargs = mock_get.call_args[1]
        assert "timeout" in call_kwargs
        assert call_kwargs["timeout"] == (10, 35)

    @patch('rocket_alert_api.requests.get')
    def test_listenToServerEvents_streaming(self, mock_get, mock_env_vars):
        """Test listenToServerEvents enables streaming mode"""
        api = RocketAlertAPI()
        api.listenToServerEvents()

        # Verify stream=True parameter
        call_kwargs = mock_get.call_args[1]
        assert "stream" in call_kwargs
        assert call_kwargs["stream"] is True

    @patch('rocket_alert_api.requests.get')
    def test_listenToServerEvents_returns_response(self, mock_get, mock_env_vars):
        """Test listenToServerEvents returns response object"""
        mock_response = Mock()
        mock_get.return_value = mock_response

        api = RocketAlertAPI()
        result = api.listenToServerEvents()

        assert result == mock_response

    def test_user_agent_contains_chrome(self, mock_env_vars):
        """Test User-Agent header contains Chrome identifier"""
        api = RocketAlertAPI()

        assert "Chrome" in api.headers["user-agent"]
        # Typical Chrome user-agent format
        assert "Mozilla" in api.headers["user-agent"]

    @patch('rocket_alert_api.requests.get')
    def test_listenToServerEvents_all_parameters(self, mock_get, mock_env_vars):
        """Test listenToServerEvents passes all required parameters"""
        api = RocketAlertAPI()
        api.listenToServerEvents()

        # Verify call was made with all expected parameters
        call_args, call_kwargs = mock_get.call_args

        # URL as positional arg
        assert call_args[0] == "https://test-api.example.com/real-time"

        # Keyword arguments
        assert call_kwargs["headers"]["X-Test-Header"] == "test-value"
        assert call_kwargs["timeout"] == (10, 35)
        assert call_kwargs["stream"] is True
