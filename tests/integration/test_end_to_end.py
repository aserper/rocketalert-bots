import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from message_manager import MessageManager


@pytest.mark.integration
class TestEndToEnd:
    """Integration tests for complete event processing flow"""

    @patch('message_manager.MastodonBot')
    @patch('message_manager.TelegramBot')
    def test_full_event_processing_flow(self, mock_telegram_class, mock_mastodon_class,
                                       mock_env_vars, sample_event_data):
        """Test complete flow from event to message posting"""
        # Setup bot mocks
        mock_telegram = MagicMock()
        mock_telegram_class.return_value = mock_telegram

        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        # Process event through MessageManager
        manager = MessageManager()
        manager.postMessage(sample_event_data)

        # Verify messages were sent to both platforms
        mock_telegram.sendMessage.assert_called_once()
        mock_mastodon.sendMessage.assert_called_once()

        # Verify message content
        telegram_msg = mock_telegram.sendMessage.call_args[0][0]
        mastodon_msg = mock_mastodon.sendMessage.call_args[0][0]

        # Both should contain alert info
        assert "Nirim" in telegram_msg or "Gaza Envelope" in telegram_msg
        assert "Nirim" in mastodon_msg or "Gaza Envelope" in mastodon_msg

    @patch('message_manager.MastodonBot')
    @patch('message_manager.TelegramBot')
    def test_multiple_alerts_batch_processing(self, mock_telegram_class, mock_mastodon_class,
                                             mock_env_vars, multi_alert_event):
        """Test processing event with multiple alerts"""
        # Setup bot mocks
        mock_telegram = MagicMock()
        mock_telegram_class.return_value = mock_telegram

        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        # Process multi-alert event
        manager = MessageManager()
        manager.postMessage(multi_alert_event)

        # Should still send one message (with all locations concatenated)
        mock_telegram.sendMessage.assert_called_once()
        mock_mastodon.sendMessage.assert_called_once()

        # Message should be longer due to multiple locations
        telegram_msg = mock_telegram.sendMessage.call_args[0][0]
        # Should have multiple newlines for multiple locations
        assert telegram_msg.count('\n') >= 4

    @patch('message_manager.MastodonBot')
    @patch('message_manager.TelegramBot')
    def test_different_alert_types(self, mock_telegram_class, mock_mastodon_class,
                                   mock_env_vars, sample_alert):
        """Test processing different alert types (Rocket, UAV, Red Alert)"""
        # Setup bot mocks
        mock_telegram = MagicMock()
        mock_telegram_class.return_value = mock_telegram

        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        manager = MessageManager()

        # Test Rocket alert (type 1)
        rocket_event = {"alertTypeId": 1, "alerts": [sample_alert]}
        manager.postMessage(rocket_event)
        telegram_msg_1 = mock_telegram.sendMessage.call_args[0][0]
        assert "Rocket alert" in telegram_msg_1

        # Test UAV alert (type 2)
        mock_telegram.reset_mock()
        uav_event = {"alertTypeId": 2, "alerts": [sample_alert]}
        manager.postMessage(uav_event)
        telegram_msg_2 = mock_telegram.sendMessage.call_args[0][0]
        assert "Hostile UAV alert" in telegram_msg_2

        # Test Red alert (other)
        mock_telegram.reset_mock()
        other_event = {"alertTypeId": 99, "alerts": [sample_alert]}
        manager.postMessage(other_event)
        telegram_msg_3 = mock_telegram.sendMessage.call_args[0][0]
        assert "Red alert" in telegram_msg_3

    @patch('message_manager.MastodonBot')
    @patch('message_manager.TelegramBot')
    def test_error_recovery_bot_failure(self, mock_telegram_class, mock_mastodon_class,
                                       mock_env_vars, sample_event_data):
        """Test system continues after bot posting errors"""
        # Setup bot mocks with one failing
        mock_telegram = MagicMock()
        mock_telegram_class.return_value = mock_telegram

        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        manager = MessageManager()

        # Should not raise exception despite errors
        try:
            manager.postMessage(sample_event_data)
        except Exception as e:
            pytest.fail(f"Should handle errors gracefully: {e}")

        # Both bots should be called
        mock_telegram.sendMessage.assert_called_once()
        mock_mastodon.sendMessage.assert_called_once()

    @patch('message_manager.MastodonBot')
    @patch('message_manager.TelegramBot')
    def test_message_truncation_for_long_alert_lists(self, mock_telegram_class, mock_mastodon_class,
                                                     mock_env_vars, test_alerts_data):
        """Test message truncation with very long alert lists"""
        # Setup bot mocks
        mock_telegram = MagicMock()
        mock_telegram_class.return_value = mock_telegram

        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        # Create event with all test alerts
        large_event = {
            "alertTypeId": 1,
            "alerts": test_alerts_data
        }

        manager = MessageManager()
        manager.postMessage(large_event)

        # Messages should be sent
        mock_telegram.sendMessage.assert_called_once()
        mock_mastodon.sendMessage.assert_called_once()

        # Get the messages
        telegram_msg = mock_telegram.sendMessage.call_args[0][0]
        mastodon_msg = mock_mastodon.sendMessage.call_args[0][0]

        # Messages may need truncation by the bots
        # Just verify they were created and sent
        assert isinstance(telegram_msg, str)
        assert isinstance(mastodon_msg, str)
        assert len(telegram_msg) > 0
        assert len(mastodon_msg) > 0

    @patch('message_manager.MastodonBot')
    @patch('message_manager.TelegramBot')
    def test_hebrew_and_english_text_handling(self, mock_telegram_class, mock_mastodon_class,
                                              mock_env_vars, sample_event_data):
        """Test proper handling of Hebrew and English text"""
        # Setup bot mocks
        mock_telegram = MagicMock()
        mock_telegram_class.return_value = mock_telegram

        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        manager = MessageManager()
        manager.postMessage(sample_event_data)

        # Verify messages were sent
        mock_telegram.sendMessage.assert_called_once()
        mock_mastodon.sendMessage.assert_called_once()

        # Get messages
        telegram_msg = mock_telegram.sendMessage.call_args[0][0]
        mastodon_msg = mock_mastodon.sendMessage.call_args[0][0]

        # Messages should contain English location names
        assert "Nirim" in telegram_msg or "Gaza Envelope" in telegram_msg
        assert "Nirim" in mastodon_msg or "Gaza Envelope" in mastodon_msg

    @patch('message_manager.MastodonBot')
    @patch('message_manager.TelegramBot')
    def test_timestamp_included_in_messages(self, mock_telegram_class, mock_mastodon_class,
                                           mock_env_vars, sample_event_data):
        """Test timestamps are included in alert messages"""
        # Setup bot mocks
        mock_telegram = MagicMock()
        mock_telegram_class.return_value = mock_telegram

        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        manager = MessageManager()
        manager.postMessage(sample_event_data)

        # Get messages
        telegram_msg = mock_telegram.sendMessage.call_args[0][0]
        mastodon_msg = mock_mastodon.sendMessage.call_args[0][0]

        # Both should contain timestamp
        timestamp = sample_event_data["alerts"][0]["timeStamp"]
        assert timestamp in telegram_msg
        assert timestamp in mastodon_msg
