import os
import sys
from telebot import TeleBot

# Telegram's message character limit
MAX_CHARACTERS = 4096
TELEGRAM_FOOTER = "[RocketAlert.live](https://RocketAlert.live)"

class TelegramBot:
    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            print("CRITICAL ERROR: TELEGRAM_BOT_TOKEN environment variable not set.", flush=True)
            sys.exit(1)

        self.channel = os.environ.get("TELEGRAM_CHANNEL_ID", "@RocketAlert")
        self.bot = TeleBot(self.bot_token)

        print("DEBUG: Initializing TelegramBot...", flush=True)

        # Test connection by getting bot info
        try:
            bot_info = self.bot.get_me()
            print(f"DEBUG: Connected as @{bot_info.username}", flush=True)
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to connect to Telegram: {e}", flush=True)
            sys.exit(1)

    def sendMessage(self, content):
        print("      To Telegram...", end="", flush=True)
        content = f"{content}{TELEGRAM_FOOTER}"
        if len(content) > MAX_CHARACTERS:
            content = self.truncateToMaxMessageSize(content)
        else:
            if not isinstance(content, (list)):
                content = [content]

        try:
            for message in content:
                self.bot.send_message(
                    chat_id=self.channel,
                    text=message,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
        except Exception as e:
            print(f"Error posting message to Telegram: {e}", flush=True)
        print("done.", flush=True)

    # Splits a message string whose length > MAX_CHARACTERS into a list of
    # messages, the length of each  of which < MAX_CHARACTERS
    def truncateToMaxMessageSize(self, content):
        truncatedMessages = []
        newMessage = ""
        for line in content.splitlines():
            if len(newMessage) + len(line) +1 < MAX_CHARACTERS:
                newMessage = f"{newMessage}{line}\n"
            else:
                if newMessage:
                    truncatedMessages.append(newMessage)
                newMessage = f"{line}\n"
        if newMessage:
            truncatedMessages.append(newMessage)

        return truncatedMessages
