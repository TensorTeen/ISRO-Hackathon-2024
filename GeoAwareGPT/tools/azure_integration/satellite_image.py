import os
import math
import requests
from typing import Tuple
from PIL import Image

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.maps.render import MapsRenderClient

from ...schema import AzureTool


# def authenticate(mode=os.getenv("AZURE_AUTH_MODE", "SKA")):
#     """
#     Authenticates the user with Azure. If the mode is set to "SKA", 
#         uses shared key authentication. Otherwise, uses microsoft entra (I think)
#     Args:
#         mode (str, optional): The mode of authentication ('SKA' or 'Entra'). Defaults to 
#             os.getenv("AZURE_AUTH_MODE", "SKA").
#     """
#     from dotenv import load_dotenv
#     if mode == "SKA":
#         return AzureKeyCredential(os.environ["AZURE_SUBSCRIPTION_KEY"])
#     elif mode == "Entra":
#         return DefaultAzureCredential()
#     else:
#         raise ValueError("Invalid mode. Must be 'SKA' or 'Entra'.")
def lat_long_to_tile_xy(latitude, longitude, zoom):
    # Ensure latitude and longitude are within bounds
    if latitude < -85.05112878:
        latitude = -85.05112878
    elif latitude > 85.05112878:
        latitude = 85.05112878

    # Convert latitude and longitude to radians
    lat_rad = math.radians(latitude)

    # Number of tiles in each dimension at the given zoom level
    n = 2.0**zoom

    # Calculate X tile coordinate
    x_tile = (longitude + 180.0) / 360.0 * n

    # Calculate Y tile coordinate
    y_tile = (
        (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi)
        / 2.0
        * n
    )

    # Return the tile x, y as integers
    return int(x_tile), int(y_tile)


class SatelliteImage(AzureTool):
    def __init__(self, config=None):
        """Note: this authenticates with Entra or whatever"""
        super().__init__(
            config=config,
            name="satellite_image",
            description="A tool to get satellite images from bounding box coordinates",
            version="0.1",
        )
        self.tool_type = "AU"
        self.tool_output = "image"
        self.ska = os.environ['AZURE_SUBSCRIPTION_KEY']
        print(f'{self.ska=}')
    def run(self, bbox: Tuple[float, float, float, float]) -> Image.Image:
        tilesetId = "microsoft.imagery"
        bounding_box = ','.join(map(str, bbox))
        uri = f'https://atlas.microsoft.com/map/static?api-version=2024-04-01&tilesetId={tilesetId}&bbox={bounding_box}&view=IN&subscription-key={self.ska}'
        print(uri)
        raise Exception("Not implemented")
        result: requests.Response = requests.get()
        try:
            img = Image.open(result.content)
        except Exception as e:
            print(result)
            raise e
        return img
    
def main():
    # python -m GeoAwareGPT.tools.azure_integration.satellite_image
    tool = SatelliteImage()
    img = tool.run((13.08784, 80.27847, 13.08785, 80.27848))
    img.save("test_satellite_img.png")
    img.show()
if __name__ == '__main__':
    main()