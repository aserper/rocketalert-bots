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
            # Custom header to please CF
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0"
        }

    def listenToServerEvents(self):
        print(f"DEBUG: Connecting to {self.baseURL}/real-time?alertTypeId=-1...", flush=True)
        # Log headers safely (masking custom header value if possible, but for now just showing keys is safer or strict specific masking)
        safe_headers = self.headers.copy()
        if self.customHeaderKey in safe_headers:
             safe_headers[self.customHeaderKey] = "***REDACTED***"
        print(f"DEBUG: Request Headers: {safe_headers}", flush=True)
        
        # Timeout: (connect_timeout, read_timeout)
        # Connect: 10s (fail fast if network down)
        # Read: 60s (3x keep-alive interval of 20s - very conservative)
        return requests.get(f"{self.baseURL}/real-time?alertTypeId=-1", headers=self.headers, stream=True, timeout=(10, 60))
