# from datetime import date
import requests
import os
class RocketAlertAPI:
    def __init__(self):
        self.baseURL = os.environ['RA_BASEURL']
        self.customHeaderValue = os.environ['CUSTOM_HEADER_VALUE']
        self.customHeaderKey = os.environ['CUSTOM_HEADER_KEY']
        self.headers = {
            self.customHeaderKey: self.customHeaderValue,
            # Custom header to please CF
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0"
        }

    def listenToServerEvents(self):
        return requests.get(f"{self.baseURL}/real-time", headers=self.headers, stream=True, timeout=120)
