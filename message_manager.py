
from telegram_bot import TelegramBot
from mastodon_bot import MastodonBot
from message_builder import AlertMessageBuilder

class MessageManager:
    def postMessage(self, content):
        print("Building alert message...")
        content = AlertMessageBuilder().buildAlerts(content)
        print(content)

        mastodonFooter = "https://RocketAlert.live"
        MastodonBot().sendMessage(f"{content}{mastodonFooter}")
        print("Message posted to Mastodon.")

        telegtamFooter = "[RocketAlert.live](https://RocketAlert.live)"
        TelegramBot().sendMessage(f"{content}{telegtamFooter}")
        print("Message posted to Telegram.")
