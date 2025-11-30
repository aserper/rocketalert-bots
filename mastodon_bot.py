import os
from mastodon import Mastodon

# Mastodon's toot character limit
MAX_CHARACTERS = 500

class MastodonBot:
    def __init__(self):
        self.api_baseurl = os.environ["MASTO_BASEURL"]
        self.accessToken = os.environ["MASTO_ACCESS_TOKEN"]
        self.mastodon = Mastodon(
            api_base_url=self.api_baseurl,
            access_token=self.accessToken,
            request_timeout=30
        )

    def sendMessage(self, content):
        if len(content) > MAX_CHARACTERS:
            content = self.truncateToMaxMessageSize(content)

        if not isinstance(content, (list)):
            content = [content]

        try:
            for message in content:
                # if file is None:
                self.mastodon.status_post(message)
                # else:
                #     try:
                #         media_ids=self.mastodon.media_post(media_file=file, mime_type="image/png")
                #         self.mastodon.status_post(message, media_ids=media_ids)
                #     except Exception as e:
                #         self.mastodon.status_post(message)
                    
        except Exception as e:
            print(f"Error posting message to Mastodon: {e}", flush=True)
                

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