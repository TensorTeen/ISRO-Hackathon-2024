from azure.core.credentials import AzureKeyCredential
from azure.maps.render import MapsRenderClient
import os
from dotenv import load_dotenv
from PIL import Image
import io
import math

load_dotenv()
env = os.environ["AZURE_SUBSCRIPTION_KEY"]
print(f'{env=}')
credential = AzureKeyCredential(env)

render_client = MapsRenderClient(
    credential=credential,
)


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


x, y = lat_long_to_tile_xy(13.08784, 80.27847, 15)   
z= 15
result = render_client.get_map_tile(
    tileset_id="microsoft.imagery",
    x=x,
    y=y,
    z=z,
)


# Convert the image to a PIL image

with open("map_static_image.png", "wb") as file:
    for x in result:
        file.write(x)
