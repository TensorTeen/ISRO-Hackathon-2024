import os
import math
import requests
from typing import Tuple, Callable
from functools import wraps
from PIL import Image
from collections.abc import Iterator
import io
import asyncio

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
def make_async(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        result = await asyncio.to_thread(func, *args, **kwargs)
        return result
    return wrapper
def fake_make_async(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result
    return wrapper

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
        """Note: this authenticates with SKA"""
        super().__init__(
            config=config,
            name="satellite_image",
            description="A tool to get satellite images from latitude, longitude and zoom level",
            version="0.1",
        )
        self.tool_type = "AU"
        self.tool_output = "image"
        self.credential = AzureKeyCredential(os.environ['AZURE_SUBSCRIPTION_KEY'])
        self.render_client = MapsRenderClient(
            credential=self.credential,
            # client_id=os.environ['AZURE_CLIENT_ID'],
        )
        # self.ska = os.environ['AZURE_SUBSCRIPTION_KEY']
        # print(f'{self.ska=}')
    async def run(self, latitude: float, longitude: float, zoom: int) -> Image.Image:
        """
        Get satellite image from latitude, longitude

        Args:
            lati
        """
        x, y = lat_long_to_tile_xy(latitude, longitude, zoom)
        get_tile = make_async(MapsRenderClient.get_map_tile)
        result: Iterator[bytes] = await get_tile(
            self.render_client,
            tileset_id="microsoft.imagery",
            x=x,
            y=y,
            z=zoom,
        )
        @make_async
        def load_image(result: Iterator[bytes]) -> Image.Image:
            img_file = io.BytesIO()
            for chunk in result:
                img_file.write(chunk)
            img: Image.Image = Image.open(img_file)
            try:
                img.load()
            except OSError as e:
                raise ValueError(f"Could not load image") from e
            return img
        return await load_image(result)
async def main():
    # python -m GeoAwareGPT.tools.azure_integration.satellite_image
    tool = SatelliteImage()
    img = await tool.run(13.08784, 80.27847, 4)
    img.save("test_satellite_img.png")
    img.show()
if __name__ == '__main__':
    asyncio.run(main())