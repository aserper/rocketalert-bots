
from telegram_bot import TelegramBot
from mastodon_bot import MastodonBot
from twitter_bot import TwitterBot
from message_builder import AlertMessageBuilder

class MessageManager:
    def postMessage(self, content):
        print("Building alert message...")
        content = AlertMessageBuilder().buildAlerts(content)
        print(content)

        MastodonBot().sendMessage(content)
        print("Message posted to Mastodon.")

        telegtamFooter = "[RocketAlert.live](https://RocketAlert.live)"
        TelegramBot().sendMessage(f"{content}{telegtamFooter}")
        print("Message posted to Telegram.")

        TwitterBot().sendMessage(content)
        print("Message posted to Twitter.")
