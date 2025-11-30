import pytest
from unittest.mock import Mock, patch, MagicMock, call
from message_manager import MessageManager


@pytest.mark.unit
class TestMessageManager:
    """Tests for MessageManager class"""

    @patch('message_manager.MastodonBot')
    @patch('message_manager.TelegramBot')
    @patch('message_manager.AlertMessageBuilder')
    def test_init_creates_bots(self, mock_builder, mock_telegram, mock_mastodon, mock_env_vars):
        """Test MessageManager initialization creates bot instances"""
        manager = MessageManager()

        mock_builder.assert_called_once()
        mock_telegram.assert_called_once()
        mock_mastodon.assert_called_once()

    @patch('message_manager.MastodonBot')
    @patch('message_manager.TelegramBot')
    @patch('message_manager.AlertMessageBuilder')
    def test_postMessage_single_alert(self, mock_builder_class, mock_telegram_class,
                                     mock_mastodon_class, mock_env_vars, sample_event_data):
        """Test postMessage processes single alert correctly"""
        # Setup mocks
        mock_builder = MagicMock()
        mock_builder.buildAlert.return_value = "Nirim - Gaza Envelope"
        mock_builder.buildMessage.return_value = {
            "text": "Test message",
            "file": None
        }
        mock_builder_class.return_value = mock_builder

        mock_telegram = MagicMock()
        mock_telegram_class.return_value = mock_telegram

        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        manager = MessageManager()
        manager.postMessage(sample_event_data)

        # Verify buildAlert was called
        mock_builder.buildAlert.assert_called_once()

        # Verify both bots sent messages
        mock_telegram.sendMessage.assert_called_once()
        mock_mastodon.sendMessage.assert_called_once()

    @patch('message_manager.MastodonBot')
    @patch('message_manager.TelegramBot')
    @patch('message_manager.AlertMessageBuilder')
    def test_postMessage_multiple_alerts(self, mock_builder_class, mock_telegram_class,
                                        mock_mastodon_class, mock_env_vars, multi_alert_event):
        """Test postMessage handles multiple alerts in one event"""
        # Setup mocks
        mock_builder = MagicMock()
        mock_builder.buildAlert.return_value = "Test Location"
        mock_builder.buildMessage.return_value = {
            "text": "Test message",
            "file": None
        }
        mock_builder_class.return_value = mock_builder

        mock_telegram = MagicMock()
        mock_telegram_class.return_value = mock_telegram

        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        manager = MessageManager()
        manager.postMessage(multi_alert_event)

        # Should call buildAlert for each alert
        assert mock_builder.buildAlert.call_count == 5

    @patch('message_manager.MastodonBot')
    @patch('message_manager.TelegramBot')
    @patch('message_manager.AlertMessageBuilder')
    def test_postMessage_telegram_footer_added(self, mock_builder_class, mock_telegram_class,
                                               mock_mastodon_class, mock_env_vars, sample_event_data):
        """Test postMessage adds RocketAlert.live footer to Telegram"""
        # Setup mocks
        mock_builder = MagicMock()
        mock_builder.buildAlert.return_value = "Nirim - Gaza Envelope"
        mock_builder.buildMessage.return_value = {
            "text": "Alert message",
            "file": None
        }
        mock_builder_class.return_value = mock_builder

        mock_telegram = MagicMock()
        mock_telegram_class.return_value = mock_telegram

        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        manager = MessageManager()
        manager.postMessage(sample_event_data)

        # Verify Telegram message includes footer
        telegram_call_args = mock_telegram.sendMessage.call_args[0][0]
        assert "[RocketAlert.live](https://RocketAlert.live)" in telegram_call_args

    @patch('message_manager.MastodonBot')
    @patch('message_manager.TelegramBot')
    @patch('message_manager.AlertMessageBuilder')
    def test_postMessage_mastodon_no_footer(self, mock_builder_class, mock_telegram_class,
                                           mock_mastodon_class, mock_env_vars, sample_event_data):
        """Test postMessage doesn't add footer to Mastodon"""
        # Setup mocks
        mock_builder = MagicMock()
        mock_builder.buildAlert.return_value = "Nirim - Gaza Envelope"
        mock_builder.buildMessage.return_value = {
            "text": "Alert message",
            "file": None
        }
        mock_builder_class.return_value = mock_builder

        mock_telegram = MagicMock()
        mock_telegram_class.return_value = mock_telegram

        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        manager = MessageManager()
        manager.postMessage(sample_event_data)

        # Verify Mastodon message doesn't include footer
        mastodon_call_args = mock_mastodon.sendMessage.call_args[0][0]
        assert "[RocketAlert.live]" not in mastodon_call_args

    @patch('message_manager.MastodonBot')
    @patch('message_manager.TelegramBot')
    @patch('message_manager.AlertMessageBuilder')
    def test_postMessage_bot_error_handling(self, mock_builder_class, mock_telegram_class,
                                           mock_mastodon_class, mock_env_vars, sample_event_data):
        """Test postMessage continues despite bot failures"""
        # Setup mocks
        mock_builder = MagicMock()
        mock_builder.buildAlert.return_value = "Nirim - Gaza Envelope"
        mock_builder.buildMessage.return_value = {
            "text": "Alert message",
            "file": None
        }
        mock_builder_class.return_value = mock_builder

        mock_telegram = MagicMock()
        mock_telegram.sendMessage.side_effect = Exception("Telegram error")
        mock_telegram_class.return_value = mock_telegram

        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        manager = MessageManager()

        # Should not raise exception
        try:
            manager.postMessage(sample_event_data)
        except Exception:
            pytest.fail("postMessage should handle bot errors gracefully")

    @patch('message_manager.MastodonBot')
    @patch('message_manager.TelegramBot')
    @patch('message_manager.AlertMessageBuilder')
    def test_postMessage_alert_type_handling(self, mock_builder_class, mock_telegram_class,
                                            mock_mastodon_class, mock_env_vars):
        """Test postMessage handles different alertTypeId values"""
        # Setup mocks
        mock_builder = MagicMock()
        mock_builder.buildAlert.return_value = "Test Location"
        mock_builder.buildMessage.return_value = {
            "text": "Alert message",
            "file": None
        }
        mock_builder_class.return_value = mock_builder

        mock_telegram = MagicMock()
        mock_telegram_class.return_value = mock_telegram

        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        manager = MessageManager()

        # Test different alert types
        for alert_type in [1, 2, 99]:
            event_data = {
                "alertTypeId": alert_type,
                "alerts": [{
                    "name": "Test",
                    "timeStamp": "2023-12-04 16:59:09"
                }]
            }
            manager.postMessage(event_data)

        # Should call buildMessage with correct alertTypeId
        assert mock_builder.buildMessage.call_count == 3

    @patch('message_manager.MastodonBot')
    @patch('message_manager.TelegramBot')
    @patch('message_manager.AlertMessageBuilder')
    def test_postMessage_concatenates_locations(self, mock_builder_class, mock_telegram_class,
                                               mock_mastodon_class, mock_env_vars, multi_alert_event):
        """Test postMessage concatenates multiple alert locations"""
        # Setup mocks
        mock_builder = MagicMock()
        mock_builder.buildAlert.return_value = "Location"
        mock_builder.buildMessage.return_value = {
            "text": "Alert message",
            "file": None
        }
        mock_builder_class.return_value = mock_builder

        mock_telegram = MagicMock()
        mock_telegram_class.return_value = mock_telegram

        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        manager = MessageManager()
        manager.postMessage(multi_alert_event)

        # Check that buildMessage was called with concatenated locations
        call_args = mock_builder.buildMessage.call_args
        alert_locations = call_args[0][4]  # 5th argument is alertLocations

        # Should contain newlines for multiple locations
        assert alert_locations.count('\n') >= 4  # At least 5 locations
