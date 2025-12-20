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
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def listenToServerEvents(self):
        print(f"DEBUG: Connecting to {self.baseURL}/real-time...", flush=True)
        # Timeout: (connect_timeout, read_timeout)
        # Connect: 10s (fail fast if network down)
        # Read: 35s (Keep-alives are sent every 20s. If we miss one + buffer, reconnect)
        return requests.get(f"{self.baseURL}/real-time", headers=self.headers, stream=True, timeout=(10, 35))
