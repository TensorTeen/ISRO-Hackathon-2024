import os
import io
from PIL import Image

import dotenv
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.maps.render import MapsRenderClient

dotenv.load_dotenv()
client_id = os.environ['AZURE_CLIENT_ID'] # ID of the Azure Maps resource
subscription_key = os.environ['AZURE_SUBSCRIPTION_KEY']
print(f'{client_id=}\n{subscription_key=}')
credential = DefaultAzureCredential()
# credential = AzureKeyCredential(subscription_key)

render_client = MapsRenderClient(
    credential=credential,
    client_id=client_id,
)
# result = render_client.get_copyright_for_world()
# print(result)
result = render_client.get_map_static_image(
    zoom=10, 
    center=[80.2705,13.0843],
    localized_map_view='IN',
    layer='microsoft.imagery'
)
with open('test.png', 'wb+') as f:
    for i in result:
        f.write(i)
    # try:
    #     img = Image.open(io.BytesIO(i))
    #     img.show()
    # except:
    #     print('Error in opening image portion')
# result