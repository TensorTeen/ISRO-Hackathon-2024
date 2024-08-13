import azure.maps.search as azsearch
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from ...schema import BaseTool
import requests

load_dotenv()


class Weather(BaseTool):
    def __init__(self):
        self.args: dict = {
            "latitude": "latitude of the location for which address is needed(float)",
            "longitude": "longitude of the location for which address is needed(float)",
            "severe_alerts": "Boolean to get severe weather alerts(bool)",
            "days": "Number of days behind the current date for which forecast is needed(int)(optional, default=1)",
        }  # argument: description(type)
        super().__init__(
            "get_weather",
            "A tool to get the current weather given lattitude Longitude. Weather for the previous day can also be obtained using the days parameter. Severe weather alerts can also be obtained using the severe_alerts parameter",
            "1.0",
            self.args,
        )
        # self.name = "geodecode"
        # self.description = "A tool to decode the gecoded of an address. returns the address of the geocoded location"
        # self.version = "1.0"
        self.tool_type: str = "AUA"
        self.subscription_key = os.environ["AZURE_SUBSCRIPTION_KEY"]

    # Function to get current weather conditions
    def run(self, latitude, longitude, severe_alerts=False, days=7):
        if not severe_alerts:
            url = f"https://atlas.microsoft.com/weather/currentConditions/json"
            params = {
                "api-version": "1.0",
                "query": f"{latitude},{longitude}",
                "subscription-key": self.subscription_key,
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return str(response.json())
            else:
                return str({"error": response.status_code, "message": response.text})
        elif severe_alerts and not days:
            url = f"https://atlas.microsoft.com/weather/severe/alerts/json"
            params = {
                "api-version": "1.0",
                "query": f"{latitude},{longitude}",
                "subscription-key": self.subscription_key,
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return str(response.json())
            else:
                return str({"error": response.status_code, "message": response.text})
        else:
            url = f"https://atlas.microsoft.com/weather/forecast/daily/json"
            params = {
                "api-version": "1.0",
                "query": f"{latitude},{longitude}",
                "duration": days,
                "subscription-key": self.subscription_key,
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                return str({"error": response.status_code, "message": response.text})
