# from datetime import date
import requests
import os
class RocketAlertAPI:
    def __init__(self):
        self.baseURL = os.environ['RA_BASEURL'].strip()
        self.customHeaderValue = os.environ['CUSTOM_HEADER_VALUE'].strip()
        self.customHeaderKey = os.environ['CUSTOM_HEADER_KEY'].strip()
        self.headers = {
            self.customHeaderKey: self.customHeaderValue,
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }

    def listenToServerEvents(self):
        print(f"DEBUG: Connecting to {self.baseURL}/real-time...", flush=True)
        # Log headers safely (masking custom header value if possible, but for now just showing keys is safer or strict specific masking)
        safe_headers = self.headers.copy()
        if self.customHeaderKey in safe_headers:
             safe_headers[self.customHeaderKey] = "***REDACTED***"
        print(f"DEBUG: Request Headers: {safe_headers}", flush=True)
        
        # Timeout: (connect_timeout, read_timeout)
        # Connect: 10s (fail fast if network down)
        # Read: 35s (Keep-alives are sent every 20s. If we miss one + buffer, reconnect)
        return requests.get(f"{self.baseURL}/real-time", headers=self.headers, stream=True, timeout=(10, 35))
