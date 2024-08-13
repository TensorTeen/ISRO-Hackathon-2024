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
# import streamlit as st

# st.session_state['db_engine'] = engine
# st.session_state['db_session'] = sessionmaker(bind=engine)

SYSTEM_PROMPT = """
You are a helpful conversational assistant. Below are the details about the use case which you need to abide by strictly:
<usecase_details>
you are an agent that helps users with their queries related to geography. You have access to an SQL database and a tool that you can use to execute SQL queries that can help you fetch information about a location, and more.
</usecase_details>

You are currently in a specific state of the conversational-flow described below 
Details about the current-state:
Instructions to be followed:
- The thought should be very descriptive and should include the reason for generating the given sql query.
- Make the conversation coherent. The responses generated should feel like a normal conversation. 
- Do not generate unicode characters or hindi characters at all.

Bot specific instructions to be followed: (Note: These instructions are specific to the bot type and should be followed strictly overriding the general instructions)
- Use informal, more conversational and colloquial language. Avoid decorative words and choice of too much drama in your language.
- Avoid bulleted lists, markdowns, structured outputs, and any special characters like double quotes, single quotes, or hyphen etc in your responses.
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

ONLY make use of the tables and fields mentioned below and ensure that the SQL query is valid. ENSURE THAT TABLE NAMES AND FIELD NAMES ARE VALID.
Return 'CANNOT_SOLVE' in the sql_query in case the query is not solvable with the given database, ONLY IF YOU ARE COMPLETELY CONFIDENT THAT IT CANNOT BE SOLVED.
"""


class SQLGenerator(BaseTool):
    """
    Tool for fetching coordinates using a PostgreSQL database with PostGIS extension.

    Attributes:
        session (sqlalchemy.orm.sessionmaker): Session for the database, so it
            doesn't need to be initialised repeatedly
    """
    def __init__(self, session: Optional[sessionmaker[session.Session]] = None, agent: Optional[Agent] = None):
        """
        Constructor for CoordinateTool
        Args:
            session (sqlalchemy.orm.sessionmaker): SQLAlchemy session
        """
        name = 'SQLGenerator'
        description = """Generates and executes SQL queries on a POSTGIS database containing 
        """
        version = '0.1'
        self.tool_type = 'AUA'
        super().__init__(name, description, version)
        if not session:
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
        else:
            self.session = session
        if not agent:
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
        else:
            self.agent = agent

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
                print(query)
                try:
                    result = session.execute(query)
                    rows = result.fetchall()
                    success_flag = True
                except Exception as error:
                    self.agent.add_user_message(f"ERROR: {error}. Please check the database schema and try again.")
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

        df.to_csv('database_info.csv', index = False)

        description = "Database Schema Description:\n\n"
    
        # Group by schema and table to create structured descriptions
        for (schema, table), group in df.groupby(['schema_name', 'table_name']):
            description += f"Schema: {schema}\n"
            description += f"Table: {table}\n"
            description += "Columns:\n"
            
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
                description += column_desc + "\n"
            
            description += "\n"
        
        return description

