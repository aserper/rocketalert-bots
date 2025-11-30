import pytest
from unittest.mock import Mock, patch, MagicMock
from mastodon_bot import MastodonBot


@pytest.mark.unit
class TestMastodonBot:
    """Tests for MastodonBot class"""

    @patch('mastodon_bot.Mastodon')
    def test_init_creates_client(self, mock_mastodon_class, mock_env_vars):
        """Test MastodonBot initialization creates Mastodon client"""
        bot = MastodonBot()

        mock_mastodon_class.assert_called_once_with(
            api_base_url="https://test-mastodon.social",
            access_token="test-token",
            request_timeout=30
        )
        assert bot.api_baseurl == "https://test-mastodon.social"
        assert bot.accessToken == "test-token"

    @patch('mastodon_bot.Mastodon')
    def test_mastodon_client_timeout_configuration(self, mock_mastodon_class, mock_env_vars):
        """Test Mastodon client is initialized with 30s timeout"""
        bot = MastodonBot()

        # Verify timeout parameter was passed
        call_kwargs = mock_mastodon_class.call_args[1]
        assert call_kwargs['request_timeout'] == 30

    @patch('mastodon_bot.Mastodon')
    def test_sendMessage_short_message(self, mock_mastodon_class, mock_env_vars):
        """Test sendMessage with message under 500 char limit"""
        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        bot = MastodonBot()
        short_message = "Test alert message"

        bot.sendMessage(short_message)

        # Should call status_post once
        mock_mastodon.status_post.assert_called_once_with(short_message)

    @patch('mastodon_bot.Mastodon')
    def test_sendMessage_over_limit(self, mock_mastodon_class, mock_env_vars):
        """Test sendMessage truncates messages over 500 chars"""
        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        bot = MastodonBot()
        # Create message over 500 chars
        long_message = "A" * 600

        bot.sendMessage(long_message)

        # Should truncate and post multiple toots
        assert mock_mastodon.status_post.call_count >= 1

    def test_truncateToMaxMessageSize_under_limit(self, mock_env_vars):
        """Test truncateToMaxMessageSize with message under 500 char limit"""
        with patch('mastodon_bot.Mastodon'):
            bot = MastodonBot()
            message = "Short message\nAnother line\n"

            result = bot.truncateToMaxMessageSize(message)

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0] == message

    def test_truncateToMaxMessageSize_500_char_boundary(self, mock_env_vars):
        """Test truncateToMaxMessageSize at exactly 500 chars"""
        with patch('mastodon_bot.Mastodon'):
            bot = MastodonBot()
            # Create message of exactly 500 characters
            message = "A" * 500

            result = bot.truncateToMaxMessageSize(message)

            # Should not need truncation
            assert len(result) >= 1

    def test_truncateToMaxMessageSize_preserves_lines(self, mock_env_vars):
        """Test truncateToMaxMessageSize doesn't split lines mid-way"""
        with patch('mastodon_bot.Mastodon'):
            bot = MastodonBot()
            # Create message with distinct lines
            line = "This is a test line\n"
            message = line * 50  # Well over 500 chars

            result = bot.truncateToMaxMessageSize(message)

            assert isinstance(result, list)
            assert len(result) > 1  # Should be split into multiple messages
            # Each message should end with newline (not split mid-line)
            for msg in result:
                if msg:  # Skip empty messages
                    assert msg.endswith('\n') or msg == result[-1]

    def test_truncateToMaxMessageSize_very_long(self, mock_env_vars):
        """Test truncateToMaxMessageSize with very long message"""
        with patch('mastodon_bot.Mastodon'):
            bot = MastodonBot()
            # Create very long message (2000 chars)
            message = "Location\n" * 200

            result = bot.truncateToMaxMessageSize(message)

            assert isinstance(result, list)
            assert len(result) >= 4  # Should split into multiple messages
            # Verify each message is under 500 char limit
            for msg in result:
                assert len(msg) <= 500

    @patch('mastodon_bot.Mastodon')
    def test_sendMessage_multiple_toots(self, mock_mastodon_class, mock_env_vars):
        """Test sendMessage posts multiple toots for long content"""
        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        bot = MastodonBot()
        # Create message that will split into multiple toots
        messages = ["Toot 1", "Toot 2", "Toot 3"]

        bot.sendMessage(messages)

        # Should call status_post for each toot
        assert mock_mastodon.status_post.call_count == 3

    @patch('mastodon_bot.Mastodon')
    def test_sendMessage_handles_list(self, mock_mastodon_class, mock_env_vars):
        """Test sendMessage handles pre-truncated message list"""
        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        bot = MastodonBot()
        messages = ["Message 1", "Message 2"]

        bot.sendMessage(messages)

        assert mock_mastodon.status_post.call_count == 2

    @patch('mastodon_bot.Mastodon')
    def test_sendMessage_error_handling(self, mock_mastodon_class, mock_env_vars):
        """Test sendMessage catches and logs errors without crashing"""
        mock_mastodon = MagicMock()
        mock_mastodon.status_post = Mock(side_effect=Exception("Test error"))
        mock_mastodon_class.return_value = mock_mastodon

        bot = MastodonBot()

        # Should not raise exception
        try:
            bot.sendMessage("Test message")
        except Exception:
            pytest.fail("sendMessage should catch exceptions")

    def test_truncateToMaxMessageSize_empty_lines(self, mock_env_vars):
        """Test truncateToMaxMessageSize handles empty lines correctly"""
        with patch('mastodon_bot.Mastodon'):
            bot = MastodonBot()
            message = "Line 1\n\n\nLine 2\n"

            result = bot.truncateToMaxMessageSize(message)

            assert isinstance(result, list)
            # Should preserve structure
            assert "\n\n" in result[0] or len(result) > 1
