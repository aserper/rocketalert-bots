import os
import pytwitter

class TwitterBot:
    def __init__(self):
        self.api = pytwitter.Api(
            consumer_key = os.environ["TWITTER_CONSUMER_KEY"],
            consumer_secret = os.environ["TWITTER_CONSUMER_SECRET"],
            access_token = os.environ["TWITTER_ACCESS_TOKEN"],
            access_secret = os.environ["TWITTER_ACCESS_SECRET"],
        )

    def sendMessage(self, content):
        self.api.create_tweet(text=content)
