from GeoAwareGPT.tools.database_integration.sql_bot import SQLGenerator
import asyncio

test_gen = SQLGenerator()
# result = asyncio.run(test_gen.run("Find the percentage of all land use types in chennai"))
result = asyncio.run(test_gen.run("Find the nearest water body to the point with latitude 17.5221 and longitude 78.4448. Return the name of the water body."))
print(result)
