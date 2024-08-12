import azure.maps.search as azsearch
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from ...schema import BaseTool

load_dotenv()


class GeoDecode(BaseTool):
    def __init__(self):
        self.args: dict = {
            "latitude": "latitude of the location for which address is needed(float)",
            "longitude": "longitude of the location for which address is needed(float)",
        }  # argument: description(type)
        super().__init__("geodecode", "A tool to decode the gecoded of an address. returns the address of the geocoded location", "1.0", self.args)
        # self.name = "geodecode"
        # self.description = "A tool to decode the gecoded of an address. returns the address of the geocoded location"
        # self.version = "1.0"
        self.tool_type: str = "AUA"

    def run(self, latitude, longitude):
        credential = AzureKeyCredential(os.environ["AZURE_SUBSCRIPTION_KEY"])
        # Create a search client
        search_client = azsearch.MapsSearchClient(credential)

        # Perform a search
        results = search_client.reverse_search_address(
            coordinates=(latitude, longitude)
        )
        if not results.results:
            raise ValueError("No results found")

        # Get the first result
        result = results.results[0]

        # Return the location
        return result.address

if __name__ == '__main__':
    # python -m GeoAwareGPT.tools.azure_integration.geodecode    
    tool = GeoDecode()
    print(tool.run(13.08784, 80.27847))