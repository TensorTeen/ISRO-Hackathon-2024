import azure.maps.search as azsearch
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from ...schema import BaseTool

load_dotenv()


class GeoCode(BaseTool):
    def __init__(self):
        self.name = "geocode"
        self.description = "A tool to geocode an address"
        self.version = "1.0"
        self.args: dict = {
            "address": "Address/name of the location to geocode(str)"
        }  # argument: description(type)
        self.tool_type: str = "AUA"

    def run(self, address):
        credential = AzureKeyCredential(os.getenv("AZURE_SUBSCRIPTION_KEY"))
        # Create a search client
        search_client = azsearch.MapsSearchClient(credential)

        # Perform a search
        results = search_client.search_address(query=address)
        if not results.results:
            raise ValueError("No results found")

        # Get the first result
        result = results.results[0]

        # Return the location
        return result.position
