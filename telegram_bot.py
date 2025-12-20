import os
from telethon.sync import TelegramClient

# Telegram's message character limit
MAX_CHARACTERS = 4096
TELEGRAM_FOOTER = "[RocketAlert.live](https://RocketAlert.live)"

class TelegramBot:
    def __init__(self):
        self.api_id = os.environ["TELEGRAM_API_ID"]
        self.api_hash = os.environ["TELEGRAM_API_HASH"]
        self.channel = "@RocketAlert"
        self.client = TelegramClient('/session/session_name', self.api_id, self.api_hash)
        print("DEBUG: Connecting to TelegramClient...", flush=True)
        self.client.start()
        print("DEBUG: Connected to TelegramClient.", flush=True)

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
                self.client.send_message(self.channel, message, link_preview=False)
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