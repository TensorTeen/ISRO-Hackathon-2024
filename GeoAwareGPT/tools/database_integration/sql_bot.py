import os
from typing import Optional, Dict, Any, Sequence
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, session
from GeoAwareGPT import Agent, GeminiModel, GeminiModelConfig
from GeoAwareGPT.schema import BaseTool, BaseState
import sys
import asyncio
import json
import pandas as pd


SYSTEM_PROMPT = """
You are a helpful conversational assistant. Below are the details about the use case which you need to abide by strictly:
<usecase_details>
you are an agent that helps users with their queries related to geography. You have access to an SQL database and a tool that you can use to execute SQL queries that can help you fetch information about a location, and more.
</usecase_details>

You are currently in a specific state of the conversational-flow described below 
Details about the current-state:
Instructions to be followed:
- The thought should be very descriptive and should include the reason for generating the given sql query.
- Do not generate unicode characters or hindi characters at all.

Respond to the user in the conversation strictly following the below JSON format:
{
    "thought": "...",  # Thought process of the bot to decide what content to reply with, which tool(s) to call, briefly describing reason for tool arguments as well
    "sql_query": "..."  # SQL query to be executed. End sql code with a semicolon (;)
}

PostGIS Capabilities Description:

PostGIS extends PostgreSQL to support geographic objects. Here are some of the key geospatial functions and capabilities:

1. **Geometric Functions:**
   - `ST_Area(geometry)`: Returns the area of a geometry.
   - `ST_Distance(geomA, geomB)`: Computes the distance between two geometries.
   - `ST_Length(geometry)`: Returns the length of a geometry.

2. **Spatial Relationships:**
   - `ST_Intersects(geomA, geomB)`: Checks if two geometries intersect.
   - `ST_Within(geomA, geomB)`: Checks if one geometry is within another.
   - `ST_Overlaps(geomA, geomB)`: Checks if two geometries overlap.

3. **Transformations:**
   - `ST_Transform(geometry, srid)`: Transforms a geometry to a different spatial reference system.
   - `ST_SetSRID(geometry, srid)`: Sets the SRID for a geometry.

4. **Geocoding and Reverse Geocoding:**
   - `ST_Geocode(address)`: Converts an address into geographic coordinates (requires additional setup).

5. **Raster Functions:**
   - `ST_Clip(raster, geometry)`: Clips a raster to a specified geometry.
   - `ST_Resample(raster, scale_factor)`: Resamples a raster with a given scale factor.

6. **Geospatial Indexing:**
   - PostGIS supports the creation of spatial indexes to optimize geospatial queries using GIST indexes.

These functions can be used to perform complex geospatial analyses and queries, enhancing the capabilities of your database with spatial data.

Given below are table names and their corresponding column names with example values. You are to only use the column and table names mentioned below  and using the example values figure out which columns to use. while doing string comparisons convert both sides to lower case. ENSURE THAT TABLE NAMES AND FIELD NAMES ARE VALID. Return 'CANNOT_SOLVE' in the sql_query in case the query is not solvable with the given database, only if you are confident that it cannot be solved. Do not complicate the queries.
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
        description = """Generates and executes SQL queries on a POSTGIS database containing the following tables: city boundaries, land use, aadhaar enrolment centres, waterways, natural, points, places, buildings
        """
        args = {
            "instructions": "Give detailed instructions on what the query should accomplish. The SQL generator will be given the database schema and the natural language instructions that you provide."
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
                instructions="YOUR OUTPUT SHOULD BE GROUNDED ON THE TOOL OUTPUT, DO NOT HALLUCINATE INFORMATION.",
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
            while not success_flag:
                response = await self.agent.get_assistant_response()
                try:
                    response = json.loads(response)
                    sql = response['sql_query']
                except:
                    self.agent.add_user_message("ERROR: Invalid JSON. Please enter a valid JSON following the instructions provided")
                    continue
                if "CANNOT_SOLVE" in sql:
                    return "Query cannot be solved with given data."
                query = text(sql)
                print(f"SQL QUERY: {query}")
                try:
                    result = session.execute(query)
                    rows = result.fetchall()
                    success_flag = True
                except Exception as error:
                    self.agent.add_user_message(f"ERROR: {error}. Please check the database schema and try again.")
                    session.rollback()
                    print(error)
                    continue
        return rows
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

        df.to_csv('database_info.csv', index=False)

        description = "Database Schema Description:\n\n"
        
        # Group by schema and table to create structured descriptions
        for (schema, table), group in df.groupby(['schema_name', 'table_name']):
            description += f"Schema: {schema}\n"
            description += f"Table: {table}\n"
            description += "Columns:\n"
            
            with self.session() as session:
                # Fetch a few example values for each column in the table
                sample_query = f"SELECT * FROM {schema}.{table} LIMIT 5"
                sample_result = session.execute(text(sample_query))
                sample_data = pd.DataFrame(sample_result.fetchall(), columns=sample_result.keys())
            
            for _, row in group.iterrows():
                column_desc = f"  - Column: {row['column_name']}, Type: {row['data_type']}"
                if row['is_nullable'] == 'YES':
                    column_desc += " (Nullable)"
                if pd.notna(row['max_length']):
                    column_desc += f", Max Length: {row['max_length']}"
                if pd.notna(row['numeric_precision']):
                    column_desc += f", Precision: {row['numeric_precision']}"
                if pd.notna(row['numeric_scale']):
                    column_desc += f", Scale: {row['numeric_scale']}"
                
                # Add example values if available
                if row['column_name'] in sample_data.columns:
                    if row['column_name'] == 'geom' or not any([ch in row['data_type'] for ch in ['character', 'numeric']]) or row['column_name'] == 'srtext':
                        continue
                    example_values = sample_data[row['column_name']].dropna().unique()
                    example_values_str = ', '.join(map(str, example_values[:3]))  # Take first 3 unique examples
                    if example_values_str:
                        column_desc += f", Examples: {example_values_str}"
                
                description += column_desc + "\n"
            
            description += "\n"
        print(description)
        return description


