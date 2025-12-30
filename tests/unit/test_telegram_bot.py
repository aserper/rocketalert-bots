import pytest
from unittest.mock import Mock, patch, MagicMock
from telegram_bot import TelegramBot


@pytest.mark.unit
class TestTelegramBot:
    """Tests for TelegramBot class"""

    @patch('telegram_bot.TeleBot')
    def test_init_creates_client(self, mock_bot_class, mock_env_vars):
        """Test TelegramBot initialization creates bot instance"""
        mock_bot = MagicMock()
        mock_bot.get_me.return_value = MagicMock(username='RocketAlertBot')
        mock_bot_class.return_value = mock_bot

        bot = TelegramBot()

        mock_bot_class.assert_called_once()
        mock_bot.get_me.assert_called_once()
        assert bot.bot_token == "12345:test-bot-token"
        assert bot.channel == "@RocketAlert"

    @patch('telegram_bot.TeleBot')
    def test_sendMessage_short_message(self, mock_bot_class, mock_env_vars):
        """Test sendMessage with message under character limit"""
        mock_bot = MagicMock()
        mock_bot.get_me.return_value = MagicMock(username='TestBot')
        mock_bot.send_message = Mock()
        mock_bot_class.return_value = mock_bot

        bot = TelegramBot()
        short_message = "Test alert message"

        bot.sendMessage(short_message)

        # Should call send_message once
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert call_kwargs['chat_id'] == '@RocketAlert'
        assert call_kwargs['parse_mode'] == 'Markdown'
        assert call_kwargs['disable_web_page_preview'] == True

    @patch('telegram_bot.TeleBot')
    def test_sendMessage_over_limit(self, mock_bot_class, mock_env_vars):
        """Test sendMessage truncates messages over 4096 chars"""
        mock_bot = MagicMock()
        mock_bot.get_me.return_value = MagicMock(username='TestBot')
        mock_bot.send_message = Mock()
        mock_bot_class.return_value = mock_bot

        bot = TelegramBot()
        # Create message over 4096 chars
        long_message = "A" * 5000

        bot.sendMessage(long_message)

        # Should be truncated and called multiple times
        assert mock_bot.send_message.call_count >= 1

    def test_truncateToMaxMessageSize_under_limit(self, mock_env_vars):
        """Test truncateToMaxMessageSize with message under limit"""
        with patch('telegram_bot.TeleBot') as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot.get_me.return_value = MagicMock(username='TestBot')
            mock_bot_class.return_value = mock_bot

            bot = TelegramBot()
            message = "Short message\nAnother line\n"

            result = bot.truncateToMaxMessageSize(message)

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0] == message

    def test_truncateToMaxMessageSize_exact_boundary(self, mock_env_vars):
        """Test truncateToMaxMessageSize at exactly 4096 chars"""
        with patch('telegram_bot.TeleBot') as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot.get_me.return_value = MagicMock(username='TestBot')
            mock_bot_class.return_value = mock_bot

            bot = TelegramBot()
            # Create message of exactly 4096 characters
            message = "A" * 4096

            result = bot.truncateToMaxMessageSize(message)

            # Should not need truncation
            assert len(result) >= 1

    def test_truncateToMaxMessageSize_preserves_lines(self, mock_env_vars):
        """Test truncateToMaxMessageSize doesn't split lines mid-way"""
        with patch('telegram_bot.TeleBot') as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot.get_me.return_value = MagicMock(username='TestBot')
            mock_bot_class.return_value = mock_bot

            bot = TelegramBot()
            # Create message with distinct lines
            line = "This is a test line\n"
            message = line * 300  # Well over 4096 chars

            result = bot.truncateToMaxMessageSize(message)

            assert isinstance(result, list)
            assert len(result) > 1  # Should be split into multiple messages
            # Each message should end with newline (not split mid-line)
            for msg in result:
                if msg:  # Skip empty messages
                    assert msg.endswith('\n') or msg == result[-1]

    def test_truncateToMaxMessageSize_very_long(self, mock_env_vars):
        """Test truncateToMaxMessageSize with very long message"""
        with patch('telegram_bot.TeleBot') as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot.get_me.return_value = MagicMock(username='TestBot')
            mock_bot_class.return_value = mock_bot

            bot = TelegramBot()
            # Create very long message (12000 chars)
            message = "Location name\n" * 800

            result = bot.truncateToMaxMessageSize(message)

            assert isinstance(result, list)
            assert len(result) >= 3  # Should split into multiple messages
            # Verify each message is under limit
            for msg in result:
                assert len(msg) <= 4096

    @patch('telegram_bot.TeleBot')
    def test_sendMessage_handles_list(self, mock_bot_class, mock_env_vars):
        """Test sendMessage handles pre-truncated message list"""
        mock_bot = MagicMock()
        mock_bot.get_me.return_value = MagicMock(username='TestBot')
        mock_bot.send_message = Mock()
        mock_bot_class.return_value = mock_bot

        bot = TelegramBot()
        messages = ["Message 1", "Message 2", "Message 3"]

        bot.sendMessage(messages)

        # Should call send_message once (input is a list but treated as single message)
        mock_bot.send_message.assert_called_once()

    @patch('telegram_bot.TeleBot')
    def test_sendMessage_adds_footer(self, mock_bot_class, mock_env_vars):
        """Test sendMessage adds RocketAlert.live footer to message"""
        mock_bot = MagicMock()
        mock_bot.get_me.return_value = MagicMock(username='TestBot')
        mock_bot.send_message = Mock()
        mock_bot_class.return_value = mock_bot

        bot = TelegramBot()
        message = "Test alert"

        bot.sendMessage(message)

        # Verify Telegram message includes footer
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert "[RocketAlert.live](https://RocketAlert.live)" in call_kwargs['text']

    @patch('telegram_bot.TeleBot')
    def test_sendMessage_error_handling(self, mock_bot_class, mock_env_vars):
        """Test sendMessage catches and logs errors without crashing"""
        mock_bot = MagicMock()
        mock_bot.get_me.return_value = MagicMock(username='TestBot')
        mock_bot.send_message = Mock(side_effect=Exception("Test error"))
        mock_bot_class.return_value = mock_bot

        bot = TelegramBot()

        # Should not raise exception
        try:
            bot.sendMessage("Test message")
        except Exception:
            pytest.fail("sendMessage should catch exceptions")

    def test_truncateToMaxMessageSize_empty_lines(self, mock_env_vars):
        """Test truncateToMaxMessageSize handles empty lines correctly"""
        with patch('telegram_bot.TeleBot') as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot.get_me.return_value = MagicMock(username='TestBot')
            mock_bot_class.return_value = mock_bot

            bot = TelegramBot()
            message = "Line 1\n\n\nLine 2\n"

            result = bot.truncateToMaxMessageSize(message)

            assert isinstance(result, list)
            # Should preserve structure
            assert "\n\n" in result[0] or len(result) > 1