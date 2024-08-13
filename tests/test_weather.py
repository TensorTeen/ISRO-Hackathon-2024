from GeoAwareGPT.tools.azure_integration.weather import Weather

weather = Weather()
print(weather.run(13.08784, 80.27847))
