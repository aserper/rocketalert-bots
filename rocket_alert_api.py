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

    # Gets total alerts in the give datetime range.
    # Datetime range defaults to today.
    # def getTotalAlerts(self, today=str(date.today())):
    #     url = f"{self.baseURL}/total?from={today}&to={today}"
    #     print("Fetching daily total...")
    #     response = requests.get(url, headers=self.headers).json()
        
    #     if response["success"]:
    #         print("Daily total fetched.")
    #         return response["payload"]
    #     else:
    #         print(f"getTotalAlerts() - something went wrong. Error:{response['error']}")
    #         print("Please note the function only takes dates in string format (YYYY-MM-DD).")
    
    def listenToServerEvents(self):
        return requests.get(f"{self.baseURL}/real-time?alertTypeId=-1", headers=self.headers, stream=True)
