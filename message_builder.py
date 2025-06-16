import json
import polyline
import urllib
import requests
import os

class AlertMessageBuilder:
    def __init__(self):
        self.accessToken = os.environ["MAPBOX_TOKEN"]
        self.strokeColor = "ff0000"
        self.strokeFill = "bb1b1b"
        self.styleId = "dark-v11"
        self.mapFile = "tmp_static_map"
    
        try:
            file = open("polygons.json")
            self.polygons = json.load(file)
            file.close()
        except Exception as e:
            self.polygons = None

    # Retrieves a static map from URL and writes it to disk
    def WriteMapToFile(self, url, file):
        try:
            # Retrieve map and save to a file
            with open(file, 'wb') as f:
                f.write(requests.get(url).content)
        except Exception as e:
            print(f"WriteMapToFile() - Error writing file: {e}")

    # Given an alert, returns a string in format "locationName (areaName)"
    def buildAlert(self, alert):
        areaNameHe = alert["areaNameHe"]
        areaNameEnglish = alert["areaNameEn"]
        locationNameHe = alert["name"]
        locationNameEnglish = alert["englishName"]

        name = locationNameEnglish or locationNameHe
        areaName = areaNameEnglish or areaNameHe
        
        if areaName is None:
            return name
        return f"{name} ({areaName})"   

    # Returns a static map URL with overlays and markers
    def getMapURL(self, staticMap):
        overlays = ','.join(staticMap["overlays"])
        markers = ','.join(staticMap["markers"])
        return f"https://api.mapbox.com/styles/v1/mapbox/{self.styleId}/static/{overlays},{markers}/auto/400x400@2x?padding=100&access_token={self.accessToken}"
    
    # Returns a URLEncoded polyline overlay for the alert
    # location's polygon
    def buildPolygonOverlay(self, alert):
        if not self.polygons:
            return None
        
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
    
    # Returns a concatanted string of alert type, timestamp and list of alert locations
    def buildMessageText(self, alertTypeId, timestamp, alertLocations):
        if (alertTypeId == 1):
            header = "Rocket alert"
        elif (alertTypeId == 2):
            header = "Hostile UAV alert"
        else:
            header = "Red alert"
        header += f" {timestamp}:"
        return f"{header}\n\n" \
                f"{alertLocations}\n"
    
    def addStaticMapData(self, alert, staticMap):
        overlay = self.buildPolygonOverlay(alert)
        if overlay is not None:
            staticMap["overlays"].append(overlay)
        marker = self.buildMarker(alert)
        staticMap["markers"].append(marker)
        return staticMap

    # Returns a Message dict which includes the its text and map filename, after writing map to disk
    def buildMessage(self, staticMap, mapFileCount, alertTypeId, timestamp, alertLocations):
        # url = self.getMapURL(staticMap)
        # filename = f"{self.mapFile}_{mapFileCount}.png"
        # self.WriteMapToFile(url, filename)
        text = self.buildMessageText(alertTypeId, timestamp, alertLocations)
        # message = {"text": text, "file": filename}
        message = {"text": text}
        print("  Built message:")
        # print(f"    File: {filename}")
        print(f"    Text:")
        print(f"    {text}")
        return message