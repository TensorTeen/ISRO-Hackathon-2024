import requests
from PIL import Image
from io import BytesIO


def get_satellite_imagery(api_key, latitude, longitude, zoom=18, width=512, height=512):
    # Define the URL for the Azure Maps Satellite Imagery service
    url = f"https://atlas.microsoft.com/map/static/png?api-version=1.0&style=satellite&zoom={zoom}&center={longitude},{latitude}&width={width}&height={height}&subscription-key={api_key}"

    # Make the request to the Azure Maps API
    response = requests.get(url)   

    # Check if the request was successful
    if response.status_code == 200:
        # Open the image from the response content
        image = Image.open(BytesIO(response.content))
        return image
    else:
        print(f"Error: {response.text}")
        return None


# Replace with your Azure Maps API key
api_key = "MOs5WrVS3aBynf5FkgErz3Zfm95SMhRYUV1xX9W1E7ctYmrA353cJQQJ99AHAC5RqLJTKi2eAAAgAZMP3OkI"

# Example coordinates (latitude and longitude)
latitude = 37.7749  # San Francisco
longitude = -122.4194

# Get the satellite imagery
image = get_satellite_imagery(api_key, latitude, longitude)

# Display the image
if image:
    image.show()
