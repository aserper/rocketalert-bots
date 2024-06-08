
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
    def buildStaticMap(self, alerts):
        if not self.polygons:
            return False
        
        overlays = []
        markers = []
        for alert in alerts:
            overlay = self.buildPolygonOverlay(alert)
            markers.append(self.buildMarker(alert))
            if overlay is not None:
                overlays.append(overlay)

        overlaysString = ','.join(overlays)
        markersString = ','.join(markers)

        url = f"https://api.mapbox.com/styles/v1/mapbox/{self.styleId}/static/{overlaysString},{markersString}/auto/400x400@2x?padding=100&access_token={self.accessToken}"

        try:
            # Retrieve map and save to a file
            with open(self.mapFile, 'wb') as f:
                f.write(requests.get(url).content)
                return True
        except Exception as e:
            print(f"buildStaticMap() - Error writing file: {e}")
            return False

    # Returns a URLEncoded polyline overlay for the alert
    # location's polygon
    def buildPolygonOverlay(self, alert):
        polygon = self.polygons.get(str(alert["taCityId"]), None)
        if polygon is None:
            return None

        # Encode polygon to polyline format
        polylineEncoded = polyline.encode(polygon, 5)
        # URL encode the polyline
        URLEncoded = urllib.parse.quote(polylineEncoded.encode('utf-8'))
        overlay = f"path+{self.strokeColor}+{self.strokeFill}({URLEncoded})"
        return overlay

    # Returns a map marker encoding for the alert's coordinates
    def buildMarker(self, alert):
        lat = str(alert["lat"])
        lon = str(alert["lon"])
        return f"pin-s+{self.strokeColor}({lon},{lat})"

    def postMessage(self, eventData):
        print("Building alert message...")
        content = AlertMessageBuilder().buildAlerts(eventData)
        print(content)

        print("Generating static map...")
        hasMap = self.buildStaticMap(eventData["alerts"])
        file = self.mapFile if hasMap else None

        print("Sending message...")
        telegtamFooter = "[RocketAlert.live](https://RocketAlert.live)"
        TelegramBot().sendMessage(f"{content}{telegtamFooter}", file)

        MastodonBot().sendMessage(content, file)

        # Disabling posting to Twitter for now as current tier limit doesn't support our use case.
        # TwitterBot().sendMessage(content)
        # print("Message posted to Twitter.")
