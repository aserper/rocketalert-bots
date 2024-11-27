
from telegram_bot import TelegramBot
from mastodon_bot import MastodonBot
from message_builder import AlertMessageBuilder
import os

class MessageManager:
    def __init__(self):
        self.mapFileCount = 0
        # Maxbox request length limitation
        self.MAP_MAX_REQUEST_LENGTH = 8192
        self.messageBuilder = AlertMessageBuilder()

    def postMessage(self, eventData):
        print("Building alert message...")

        alerts = eventData["alerts"]
        if not isinstance(alerts, (list)):
            alerts = [alerts]

        alertTypeId = eventData["alertTypeId"]
        timestamp = alerts[0]["timeStamp"]
        mapFileCount = 0
        alertLocations = ""
        staticMap = {'overlays': [], 'markers': []}
        messages = []

        for idx, alert in enumerate(alerts):
            alertLocation = f"{self.messageBuilder.buildAlert(alert)}"
            self.messageBuilder.addStaticMapData(alert, staticMap)
            url = self.messageBuilder.getMapURL(staticMap)
            # If we've reached URL's max length, we:
            # Remove most recently added overlay and marker from the collection,
            # Build a new message with the current collection of overlays and markers, to be send later,
            # Start a new collection for next messages, beginning with the overlay and marker we just removed
            if len(url) > self.MAP_MAX_REQUEST_LENGTH:
                # Remove
                lastOverlay = staticMap["overlays"].pop()
                lastMarker = staticMap["markers"].pop()

                # Build
                message = self.messageBuilder.buildMessage(staticMap, mapFileCount, alertTypeId, timestamp, alertLocations)
                messages.append(message)

                # Start
                mapFileCount += 1
                staticMap["overlays"] = [lastOverlay]
                staticMap["markers"] = [lastMarker]
                alertLocations = f"{alertLocation}\n"
            else:
                alertLocations += f"{alertLocation}\n"

        message = self.messageBuilder.buildMessage(staticMap, mapFileCount, alertTypeId, timestamp, alertLocations)
        messages.append(message)
        
        telegtamFooter = "[RocketAlert.live](https://RocketAlert.live)"
        print("  Posting:")
        for idx, message in enumerate(messages):
            file = message["file"]
            text = message["text"]
        
            try:
                if os.path.isfile(file):
                    print(f"    Message {idx + 1}/{len(messages)}:")
                    print("      To Telegram...", end="")
                    TelegramBot().sendMessage(f"{text}{telegtamFooter}", file)
                    print("done.")
                    print("      To Mastodon...", end="")
                    MastodonBot().sendMessage(text, file)
                    print("done.")
                    os.remove(file)
            except Exception as e:
                print(f"Error postMessage(): {e}")