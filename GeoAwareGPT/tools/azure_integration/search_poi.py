import azure.maps.search as azsearch
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
import json
from ...schema import BaseTool

load_dotenv()


class SearchPOI(BaseTool):
    def __init__(self):
        self.name = "SearchPOI"
        self.description = (
            "A tool to find the nearby landmarks given gecoded location and a query"
        )
        self.version = "1.0"
        self.args: dict = {
            "latitude": "latitude of the location for which address is needed(float)",
            "longitude": "longitude of the location for which address is needed(float)",
            "query": "query to search for nearby landmarks(str)",
            "k": "(optional)number of landmarks to return(int)",
        }  # argument: description(type)
        self.tool_type: str = "AUA"

    def run(self, latitude, longitude, query, k=3):
        credential = AzureKeyCredential(os.getenv("AZURE_SUBSCRIPTION_KEY"))
        # Create a search client
        search_client = azsearch.MapsSearchClient(credential)

        # Perform a search
        results = search_client.search_point_of_interest_category(
            coordinates=(latitude, longitude), query=query.upper()
        )
        if not results.results:
            raise ValueError("No results found")

        # Get the first result
        result = [
            self.convert_to_string(r.point_of_interest) for r in results.results[:k]
        ]
        # Return the location
        return result

    def convert_to_string(self, result):
        converted_result = {}
        converted_result["name"] = str(result.name)
        converted_result["phone"] = str(result.phone)
        converted_result["category"] = str(result.additional_properties)
        converted_result["url"] = str(result.url)
        converted_result["opening_hours"] = str(result.operating_hours)

        return json.dumps(converted_result, indent=4)


if __name__ == "__main__":
    latitude = 47.608013
    longitude = -122.335167
    tool = SearchPOI()
    print(tool.run(latitude=latitude, longitude=longitude, query="hospital"))
