
import pytest
from unittest.mock import patch
from telegram_bot import TelegramBot
from mastodon_bot import MastodonBot

@pytest.mark.unit
class TestTruncationFixes:
    """Tests specifically for the data loss bug in truncation logic"""

    def verify_truncation(self, bot_class, env_vars, max_chars, num_lines=1000):
        with patch.dict('os.environ', env_vars):
            patch_target = 'telegram_bot.TelegramClient' if bot_class == TelegramBot else 'mastodon_bot.Mastodon'
            with patch(patch_target):
                bot = bot_class()

                # Create a message where lines are distinct numbers so we can detect missing ones.
                lines = []
                for i in range(num_lines):
                    lines.append(f"Line {i:04d}")

                content = "\n".join(lines)

                chunks = bot.truncateToMaxMessageSize(content)

                # Check if every line is present in one of the chunks.
                for line in lines:
                    found = False
                    for chunk in chunks:
                        if line in chunk:
                            found = True
                            break
                    assert found, f"Line '{line}' was lost during truncation in {bot_class.__name__}!"

                # Also verify that no chunk exceeds the limit
                for i, chunk in enumerate(chunks):
                    assert len(chunk) <= max_chars, f"Chunk {i} in {bot_class.__name__} exceeds max characters ({len(chunk)} > {max_chars})"

    def test_telegram_truncation_no_data_loss(self):
        """Verify TelegramBot truncation does not lose data when buffer fills up"""
        self.verify_truncation(
            TelegramBot,
            {'TELEGRAM_API_ID': '12345', 'TELEGRAM_API_HASH': 'hash'},
            4096
        )

    def test_mastodon_truncation_no_data_loss(self):
        """Verify MastodonBot truncation does not lose data when buffer fills up"""
        self.verify_truncation(
            MastodonBot,
            {'MASTO_BASEURL': 'https://example.com', 'MASTO_ACCESS_TOKEN': 'token'},
            500
        )
