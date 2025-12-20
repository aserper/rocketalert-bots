
import pytest
from unittest.mock import MagicMock, patch
from message_manager import MessageManager

@pytest.mark.perf
class TestStress:
    """Stress tests for high volume scenarios"""

    @patch('message_manager.MastodonBot')
    @patch('message_manager.TelegramBot')
    @patch('message_manager.AlertMessageBuilder')
    def test_massive_alert_volume(self, mock_builder_class, mock_telegram_class, 
                                 mock_mastodon_class):
        """test ability to handle 500 simultaneously alerts"""
        
        # Setup mocks
        mock_builder = MagicMock()
        # Return a realistic length string for each alert (approx 20-30 chars)
        mock_builder.buildAlert.side_effect = lambda alert: f"{alert['name']} ({alert['areaNameEn']})"
        
        # When buildMessage is called, return a dummy message. 
        # In reality, buildMessage constructs the huge string, but since we are mocking MessageBuilder,
        # we need to simulate the MessageManager's handling of the result.
        # WAIT: MessageManager calls buildMessage once at the end. 
        # The performance bottleneck we are worried about is likely in the *loop* accumulating strings
        # OR in the *TelegramBot* splitting the huge string.
        
        # Let's NOT mock the MessageBuilder heavily, or better yet, let's verify the MessageManager loop 
        # and then stress test the *Bot* splitting logic specifically.
        
        # Actually, let's look at MessageManager.postMessage:
        # It loops over alerts, calls buildAlert, and appends to a string `alertLocations`.
        # Then it calls buildMessage with the huge `alertLocations` string.
        # Then it calls `bot.sendMessage(text)`.
        
        # So we need to ensure:
        # 1. The loop doesn't take forever.
        # 2. `bot.sendMessage` handles a massive string.
        
        mock_builder.buildMessage.side_effect = lambda sm, mfc, at, ts, locs: {"text": f"Header\n\n{locs}"}
        mock_builder_class.return_value = mock_builder
        
        mock_telegram = MagicMock()
        mock_telegram_class.return_value = mock_telegram
        mock_mastodon = MagicMock()
        mock_mastodon_class.return_value = mock_mastodon

        # Generate 500 alerts
        alerts = []
        for i in range(500):
            alerts.append({
                "name": f"City {i}",
                "englishName": f"City {i}",
                "areaNameHe": "Area",
                "areaNameEn": "Area",
                "lat": 0,
                "lon": 0,
                "taCityId": i,
                "timeStamp": "2023-01-01 00:00:00"
            })
            
        event_data = {
            "alertTypeId": 1,
            "alerts": alerts
        }

        # Initialize
        manager = MessageManager()
        
        # Run
        import time
        start_time = time.time()
        manager.postMessage(event_data)
        end_time = time.time()
        
        # Verification
        
        # 1. Verify executed in reasonable time (e.g. < 2 seconds for just string processing)
        duration = end_time - start_time
        print(f"\nProcessing 500 alerts took {duration:.4f} seconds")
        assert duration < 5.0, "Processing took too long!"
        
        # 2. Verify buildAlert called 500 times
        assert mock_builder.buildAlert.call_count == 500
        
        # 3. Verify bot keys were called with a massive string
        mock_telegram.sendMessage.assert_called_once()
        args = mock_telegram.sendMessage.call_args[0]
        sent_text = args[0]
        
        # Approx length: 500 * ("City NNN (Area)\n" ~ 15 chars) = ~7500 chars
        # This is > 4096, so TelegramBot internals SHOULD split it.
        # Wait, we are mocking TelegramBot here, so we aren't testing the splitting logic yet!
        # We need to test the REAL TelegramBot logic for splitting.
        
        assert len(sent_text) > 5000, "Expected a massive message text"


class TestTelegramBotStress:
    """Stress tests specifically for TelegramBot Logic"""
    
    @patch('telegram_bot.TelegramClient')
    @patch.dict('os.environ', {'TELEGRAM_API_ID': '123', 'TELEGRAM_API_HASH': 'abc'})
    def test_splitting_massive_message(self, mock_client_class):
        from telegram_bot import TelegramBot
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        bot = TelegramBot()
        
        # Create a massive message: 1000 lines, each 20 chars = 20,000 chars
        # Limit is 4096. Should split into ~5 messages.
        lines = [f"Line {i} - some content here" for i in range(1000)]
        massive_content = "\n".join(lines)
        
        bot.sendMessage(massive_content)
        
        # Verify split
        # sendMessage calls client.send_message loop.
        # We want to see how many times send_message was called.
        
        assert mock_client.send_message.call_count >= 5
        
        # Verify total characters sent roughly matches total
        total_chars_sent = 0
        for call_args in mock_client.send_message.call_args_list:
            msg = call_args[0][1] # arg 1 is message
            assert len(msg) <= 4096
            total_chars_sent += len(msg)
            
        # Note: The splitting logic might add/remove newlines, so we check approximate length
        # original length + metadata?
        # The bot adds a footer to EACH message or just once?
        # Let's check the code.
        # Code: content = f"{content}{TELEGRAM_FOOTER}" -> Adds footer ONCE at start.
        # Then truncateToMaxMessageSize splits it.
        # So sum of parts should equal (original + footer).
        
        # Wait, `truncateToMaxMessageSize` might duplicate headers? No, likely just splits.
        # Let's conservatively say it should contain all original content.
        
        assert total_chars_sent >= len(massive_content)
