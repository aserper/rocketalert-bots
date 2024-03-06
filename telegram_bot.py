import os
from telethon import TelegramClient

# Telegram's message character limit
MAX_CHARACTERS = 4096

class TelegramBot:
    def __init__(self):
        self.api_id = os.environ["TELEGRAM_API_ID"]
        self.api_hash = os.environ["TELEGRAM_API_HASH"]
        self.channel = "@RocketAlert"
        self.client = TelegramClient('session_name', self.api_id, self.api_hash)
        self.client.start()

    def sendMessage(self, content):
        if len(content) > MAX_CHARACTERS:
            content = self.truncateToMaxMessageSize(content)

        with self.client:
            self.client.loop.run_until_complete(self.__sendMessage(content))

    # Splits a message string whose length > MAX_CHARACTERS into a list of
    # messages, the length of each  of which < MAX_CHARACTERS
    def truncateToMaxMessageSize(self, content):
        truncatedMessages = []
        newMessage = ""
        for line in content.splitlines():
            if len(newMessage) + len(line) +1 < MAX_CHARACTERS:
                newMessage = f"{newMessage}{line}\n"
            else:
                truncatedMessages.append(newMessage)
                newMessage = ""
        if newMessage:
            truncatedMessages.append(newMessage)

        return truncatedMessages

    async def __sendMessage(self, messages):
        if not isinstance(messages, (list)):
            messages = [messages]
        for message in messages:
            await self.client.send_message("me", message, link_preview=False)