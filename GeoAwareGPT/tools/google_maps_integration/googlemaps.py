from ...


class GoogleMapsTool(BaseTool):
    """A subclass of BaseTool for Google Maps API.

    Attributes:
        api_key (str): The API key for Google Maps.
        client (googlemaps.Client): The Google Maps client.

    Methods:
        run(location_name: str, landmark_name: str) -> List[Dict[str, str]]: 
            Returns a list of landmarks with their addresses.
    """

    def __init__(self, api_key: str):
        super().__init__(name="GoogleMapsTool", description="Tool to interact with Google Maps API", version="1.0")
        self.api_key = api_key
        self.client = googlemaps.Client(key=self.api_key)

    def run(self, location_name: str, landmark_name: str) -> List[Dict[str, str]]:
        """Find landmarks in a given location.

        Args:
            location_name (str): The name of the location.
            landmark_name (str): The name of the landmark to search for.

        Returns:
            List[Dict[str, str]]: A list of landmarks with their addresses.
        """
        query = f"{landmark_name} in {location_name}"
        places_result = self.client.places(query=query)
        
        landmarks = []
        for place in places_result.get('results', []):
            landmark = {
                "name": place.get("name"),
                "address": place.get("formatted_address")
            }
            landmarks.append(landmark)
        
        return landmarks