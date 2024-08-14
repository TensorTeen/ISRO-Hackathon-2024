import os
from typing import Optional, Dict, Any, Sequence
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, session
from GeoAwareGPT import Agent, GeminiModel, GeminiModelConfig, AzureModel, AzureModelConfig
from GeoAwareGPT.schema import BaseTool, BaseState
import re
import sys
import asyncio
import json
import pandas as pd


SYSTEM_PROMPT = """
You are a helpful conversational assistant. Below are the details about the use case that you need to abide by strictly:

Use Case:
You are an agent that helps users with their queries related to geography. You have access to a PostGIS-enabled SQL database and a tool to execute SQL queries that can help fetch information about a location and more. The goal is to generate SQL queries that extract the required information using the database schema provided.

Instructions:
Be Descriptive: The thought should be very descriptive and should include the reasoning for generating the SQL query.
Incorporate PostGIS Functions: Leverage PostGIS capabilities, such as spatial relationships and geometric functions, when relevant to the query.
Error Handling: If the query cannot be solved due to a lack of information or an invalid schema, return "CANNOT_SOLVE" in the sql_query field. Before doing so, consider possible fallbacks or partial solutions.
Assume Reasonable Defaults: If the user's query is ambiguous, assume reasonable defaults or suggest refinements.
Example Query Structure: Ensure that the SQL query includes a WHERE clause to filter out NULL values and uses lowercase string comparisons when needed.
Spatial Index Use: If the query could be optimized with spatial indexing, include it in your reasoning.


PostGIS Capabilities:
Geometric Functions: ST_Area, ST_Distance, ST_Length.
Spatial Relationships: ST_Intersects, ST_Within, ST_Overlaps.
Transformations: ST_Transform, ST_SetSRID.
Geocoding/Reverse Geocoding: ST_Geocode (if applicable).
Raster Functions: ST_Clip, ST_Resample.
Geospatial Indexing: Use GIST indexes for spatial optimization.


Table Information:
Schema: The database contains the following tables: city boundaries, land use, aadhaar enrolment centres, waterways, natural, points, places, buildings.
Respond to the user in the conversation strictly following the below JSON format:
{
    "thought": "I identified that the user wants to retrieve geographical information about a place. The relevant table based on the schema is [table_name], and the key columns are [columns]. I will use PostGIS functions like [function_name] to perform the required spatial operations.",
    "sql_query": "SELECT ... FROM ... WHERE ...;"
}

Database and table schema:
"""


class SQLGenerator(BaseTool):
    """
    Tool for fetching coordinates using a PostgreSQL database with PostGIS extension.

    Attributes:
        session (sqlalchemy.orm.sessionmaker): Session for the database, so it doesn't need to be initialised repeatedly
    """
    def __init__(self):
        """
        Constructor for CoordinateTool
        Args:
            session (sqlalchemy.orm.sessionmaker): SQLAlchemy session
        """
        name = 'SQLGenerator'
        description = """Generates and executes SQL queries on a POSTGIS database containing the following tables: city boundaries, land use, aadhaar enrolment centres, waterways, natural, buildings, railways, roads. This requires geocoded data (latitude and longitude) for queries involving other places.
        """
        args = {
            "instructions": "Give detailed instructions on what the query should accomplish. The SQL generator will be given the database schema and the natural language instructions. ENSURE THAT COORDINATES ARE INCLUDED IN THE INSTRUCTIONS FOR ANY PLACE. Mention table names that could be relevant."
        }
        version = '0.1'
        super().__init__(name, description, version, args)
        self.tool_type = 'AUA'
        # Load environment variables from .env file
        load_dotenv()
        # https://stackoverflow.com/questions/75009761/do-we-need-to-run-load-dotenv-in-every-module 
        # (No, we don't - sets os.environ)
        # We can move this to the main module if necessary, or probably __init__.py

        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_HOST = os.getenv("DB_HOST")
        DB_PORT = os.getenv("DB_PORT")
        DB_NAME = os.getenv("DB_NAME")
        db_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(db_string, pool_pre_ping=True)
        self.session = sessionmaker(bind=engine)
        
        states = [
            BaseState(
                name="GlobalState",
                goal="To generate an SQL query to extract the relevant information from a geospatial POSTGIS database.",
                instructions="YOUR OUTPUT SHOULD BE GROUNDED ON THE DATABASE SCHEMA, DO NOT HALLUCINATE INFORMATION. THE ONLY COORDINATE INFORMATION AVAILABLE TO YOU IS THROUGH THE INSTRUCTIONS. RETURN CANNOT SOLVE ALONG WITH THE REASON IF YOU DON'T HAVE SUFFICIENT INFORMATION. DO NOT INCLUDE the geometry column in the output when querying the database. Return data in metric units when possible.",
                tools=[],
            )
        ]
        self.agent = Agent(
            model=GeminiModel(
                model_config=GeminiModelConfig(model_name="gemini/gemini-1.5-flash")
            ),
            states=states,
        )

        self.database_desc = self.get_db_description()

        self.agent.set_system_prompt(SYSTEM_PROMPT + f"\nDATABASE DESCRIPTION:\n{self.database_desc}\n")


    async def run(self, instructions: str) -> Optional[Dict[str, Any]]:
        """
        Fetch coordinates for the given place name.

        Args:
            place_name (str): Name of the place to fetch coordinates for.

        Returns:
            dict: Dictionary containing place name and coordinates, or None if not found.
        """
        result = await self.execute_instructions(instructions)
        if result:
            return result
        return None
    
    async def execute_instructions(self, instructions: str) -> Optional[Sequence]:
        with self.session() as session:
            success_flag = False
            self.agent.add_user_message(instructions)
            count = 0
            valid_flag = False
            while not success_flag:
                if count==5:
                    return None
                count+=1
                if not valid_flag:
                    response = await self.agent.get_assistant_response()
                else:
                    valid_flag = False
                pattern = '```json(.*?)```'
                matches = re.findall(pattern, response, re.DOTALL)
                json_string = matches[-1].strip() if matches else response
                try:
                    response = json.loads(json_string)
                    sql = response['sql_query']
                except:
                    print("Invalid JSON!!!")
                    print(response)
                    self.agent.add_user_message("""ERROR: Invalid JSON. Please enter a valid JSON following the instructions provided, in the same JSON format. {
                                                    "thought": "...",  # Thought process of the bot to decide what content to reply with, which tool(s) to call, briefly describing reason for tool arguments as well
                                                    "sql_query": "..."  # SQL query to be executed. End sql code with a semicolon (;)
                                                }""")
                    continue
                if "CANNOT_SOLVE" in sql:
                    return f"Query cannot be solved with given data: {response}"
                query = text(sql)
                print(f"SQL QUERY: {query}")
                try:
                    result = session.execute(query)
                    rows = result.fetchall()[:10]
                    success_flag = True
                except Exception as error:
                    self.agent.add_user_message(f"ERROR: {error}. Please check the database schema and try again.")
                    session.rollback()
                    print(error)
                    continue
                if success_flag:
                    print("Validating...")
                    valid_flag = True
                    self.agent.add_user_message(f"Query Output: {rows}.\nIf the result answers the initial instructions, simply return 'COMPLETE' in place of the SQL query. Else, continue generating SQL in the same way until satisfied. Remember to use WHERE column_name IS NOT NULL to avoid empty results.")
                    response = await self.agent.get_assistant_response()
                    if 'COMPLETE' in response:
                        print("Valid.")
                        output = []
                        for row in rows:
                            output.append(tuple([i for i in row if len(str(i))<50]))
                        return output
                    else:
                        if 'CANNOT_SOLVE' in response:
                            return f"Model failed to generate SQL query with the given instructions. {response}"
                    print(f"Not satisfied: {response}")
                    success_flag = False
        print("Exiting...")
        output = []
        for row in rows:
            if row:
                output.append(tuple([i for i in row if len(str(i))<50]))
        return output
        # return rows if rows else None

    def get_db_description(self):
        query = """
                SELECT
                    table_schema AS schema_name,
                    table_name AS table_name,
                    column_name AS column_name,
                    ordinal_position AS column_position,
                    data_type AS data_type,
                    is_nullable AS is_nullable,
                    character_maximum_length AS max_length,
                    numeric_precision AS numeric_precision,
                    numeric_scale AS numeric_scale
                FROM
                    information_schema.columns
                WHERE
                    table_schema NOT IN ('information_schema', 'pg_catalog')
                ORDER BY
                    table_schema, table_name, ordinal_position;
                """
        query = text(query)
        with self.session() as session:
            result = session.execute(query)
            rows = result.fetchall()
        df = pd.DataFrame(rows)

        description = "Database Schema Description:\n\n"
        
        # Group by schema and table to create structured descriptions
        for (schema, table), group in df.groupby(['schema_name', 'table_name']):
            if table in ['table_name', 'spatial_ref_sys', 'raster_overviews', 'raster_columns', 'places', 'points']:
                continue
            description += f"Schema: {schema}\n"
            description += f"Table: {table}\n"
            description += "Columns:\n"
            
            with self.session() as session:
                # Fetch a few example values for each column in the table
                sample_query = f"SELECT * FROM {schema}.{table} LIMIT 10"
                sample_result = session.execute(text(sample_query))
                sample_data = pd.DataFrame(sample_result.fetchall(), columns=sample_result.keys())
            
            for _, row in group.iterrows():
                column_desc = f"  - Column: {row['column_name']}, Type: {row['data_type']}"
                # if row['is_nullable'] == 'YES':
                #     column_desc += " (Nullable)"
                # if pd.notna(row['max_length']):
                #     column_desc += f", Max Length: {row['max_length']}"
                # if pd.notna(row['numeric_precision']):
                #     column_desc += f", Precision: {row['numeric_precision']}"
                # if pd.notna(row['numeric_scale']):
                #     column_desc += f", Scale: {row['numeric_scale']}"
                
                # Add example values if available
                if row['column_name'] in sample_data.columns:
                    if row['column_name'] == 'geom' or not any([ch in row['data_type'] for ch in ['character', 'numeric']]) or row['column_name'] == 'srtext':
                        continue
                    example_values = sample_data[row['column_name']].dropna().unique()
                    example_values_str = ', '.join(map(str, example_values[:5]))  # Take first 3 unique examples
                    if example_values_str:
                        column_desc += f", Examples: {example_values_str}"
                
                description += column_desc + "\n"
            
            description += "\n"
        # print(description)
        return description


