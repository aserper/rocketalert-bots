
from telegram_bot import TelegramBot
from mastodon_bot import MastodonBot
from twitter_bot import TwitterBot
from message_builder import AlertMessageBuilder
import os
import polyline
import json
import requests
import urllib

class MessageManager:
    def __init__(self):
        self.styleId = "dark-v11"
        self.accessToken = os.environ["MAPBOX_TOKEN"]
        self.mapFile = "tmp_static_map.png"
        self.strokeColor = "ff0000"
        self.strokeFill = "bb1b1b"

        try:
            file = open("polygons.json")
            self.polygons = json.load(file)
            file.close()
        except Exception as e:
            self.polygons = None

    # Retrieves a static map with a polygon path of the alert location and saves it as a file
    # Returns True if map file saved successfully, False otherwise
    def getStaticMap(self, eventData):
        if not self.polygons:
            return False
        
        polygon = self.polygons.get(str(eventData["taCityId"]), None)
        if polygon is None:
            return False
        
        # Encode polygon to polyline format
        polylineEncoded = polyline.encode(polygon, 5)
        # URL encode the polyline
        URLEncoded = urllib.parse.quote(polylineEncoded.encode('utf-8'))
        overlay = f"path+{self.strokeColor}+{self.strokeFill}({URLEncoded})"
        url = f"https://api.mapbox.com/styles/v1/mapbox/{self.styleId}/static/{overlay}/{lon},{lat},10,0/400x400@2x?access_token={self.accessToken}"

        try:
            # Retrieve map and save to a file
            with open(self.mapFile, 'wb') as f:
                f.write(requests.get(url).content)
                return True
        except Exception as e:
            print(f"getStaticMap() - Error writing file: {e}")
            return False

    def postMessage(self, eventData):
        print("Building alert message...")
        content = AlertMessageBuilder().buildAlerts(eventData)
        print(content)

        hasMap = self.getStaticMap(eventData)

        MastodonBot().sendMessage(content)
        print("Message posted to Mastodon.")

        telegramFooter = "[RocketAlert.live](https://RocketAlert.live)"
        TelegramBot().sendMessage(f"{content}{telegramFooter}", self.mapFile if hasMap else None)
        print("Message posted to Telegram.")

        TwitterBot().sendMessage(content)
        print("Message posted to Twitter.")
