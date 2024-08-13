from GeoAwareGPT.tools.database_integration.sql_bot import SQLGenerator
import asyncio

test_gen = SQLGenerator()
result = asyncio.run(test_gen.run("Find the percentage of all land use types in chennai"))
print(result)
