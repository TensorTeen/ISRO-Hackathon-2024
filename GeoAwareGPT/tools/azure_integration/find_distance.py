import requests
from ...schema import BaseTool
import os
from dotenv import load_dotenv

load_dotenv()


class FindDistance(BaseTool):
    def __init__(self):
        self.args: dict = {
            "start_lattitude": "Latitude of the starting location(float)",
            "start_longitude": "Longitude of the starting location(float)",
            "end_lattitude": "Latitude of the destination location(float)",
            "end_longitude": "Longitude of the destination location(float)",
        }  # argument: description(type)
        super().__init__(
            "find_distance",
            "A tool to calculate the route distance and time between two geocodes using Azure Maps Route API.",
            "1.0",
            self.args,
        )
        self.tool_type: str = "AUA"
        self.api_key = os.environ["AZURE_SUBSCRIPTION_KEY"]

    async def run(self, start_lattitude, start_longitude, end_lattitude, end_longitude):
        """
        Calculate the route distance and time between two geocodes using Azure Maps Route API.

        :param api_key: Azure Maps API key
        :param start_lat: Latitude of the starting location
        :param start_lon: Longitude of the starting location
        :param end_lat: Latitude of the destination location
        :param end_lon: Longitude of the destination location
        :return: A dictionary with the distance and time
        """

        # Define the endpoint and parameters
        endpoint = "https://atlas.microsoft.com/route/directions/json"
        params = {
            "api-version": "1.0",
            "subscription-key": self.api_key,
            "query": f"{start_lattitude},{start_longitude}:{end_lattitude},{end_longitude}",
            "routeType": "fastest",  # Options: fastest, shortest, etc.
            "travelMode": "car",  # Options: car, truck, pedestrian, bicycle, etc.
        }

        # Send the request to Azure Maps Route API
        response = requests.get(endpoint, params=params)
        response.raise_for_status()  # Check for errors

        # Parse the response
        data = response.json()
        if not data["routes"]:
            return {"distance": None, "time": None}

        # Extract distance and time from the response
        route = data["routes"][0]
        distance = route["summary"]["lengthInMeters"] / 1000  # Convert to kilometers
        time = route["summary"]["travelTimeInSeconds"] / 60  # Convert to minutes

        return {"distance": distance, "time": time}
