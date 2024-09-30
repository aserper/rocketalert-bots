import os
from mastodon import Mastodon

# Mastodon's toot character limit
MAX_CHARACTERS = 500

class MastodonBot:
    def __init__(self):
        self.user = os.environ["MASTO_USER"]
        self.password = os.environ["MASTO_PASSWORD"]
        self.clientId = os.environ["MASTO_CLIENTID"]
        self.clientSecret = os.environ["MASTO_CLIENTSECRET"]
        self.api_baseurl = os.environ["MASTO_BASEURL"]

    def sendMessage(self, content, file):
        if len(content) > MAX_CHARACTERS:
            content = self.truncateToMaxMessageSize(content)

        mastodon = Mastodon(
            api_base_url=self.api_baseurl,
            client_id=self.clientId,
            client_secret=self.clientSecret,
        )
        mastodon.log_in(username=self.user, password=self.password, scopes=['read', 'write'])
        
        if not isinstance(content, (list)):
            content = [content]

        try:
            for message in content:
                if file is None:
                    mastodon.status_post(message)
                else:
                    media_ids=mastodon.media_post(media_file=file, mime_type="image/png")
                    mastodon.status_post(message, media_ids=media_ids)
        except Exception as e:
            print(f"Error posting message to Mastodon: {e}")
                

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