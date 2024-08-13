from GeoAwareGPT.tools.database_integration.sql_bot import SQLGenerator
import asyncio

test_gen = SQLGenerator()
# result = asyncio.run(test_gen.run("Find the percentage of all land use types in chennai"))
result = asyncio.run(test_gen.run("Give me the residential land use data for Chennai. Use the latitude and longitude of Chennai as 13.072092 and 80.201855 to identify the specific area."))
print(result)
