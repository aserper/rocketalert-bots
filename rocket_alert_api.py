# from datetime import date
import requests
import os
class RocketAlertAPI:
    def __init__(self):
        self.baseURL = "https://agg.rocketalert.live/api/v2/alerts"
        self.customHeaderValue = os.environ['CUSTOM_HEADER_KEY']
        self.customHeaderKey = "x-ra-agg-secret"
        self.headers = {
            self.customHeaderKey: self.customHeaderValue,
            # Custom header to please CF
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0"
        }

    def listenToServerEvents(self):
        return requests.get(f"{self.baseURL}/real-time?alertTypeId=-1", headers=self.headers, stream=True)
