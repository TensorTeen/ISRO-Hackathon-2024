import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from schema.schema import BaseTool
import streamlit as st

# Load environment variables from .env file
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

db_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(db_string, pool_pre_ping=True)
st.session_state['db_engine'] = engine
st.session_state['db_session'] = sessionmaker(bind=engine)

class CoordinateTool(BaseTool):
    """
    Tool for fetching coordinates using a PostgreSQL database with PostGIS extension.

    Attributes:
        test (bool): Decides if this module is being run in test mode
    """
    def __init__(self):
        """
        Constructor for CoordinateTool

        Args:
            test_schema (bool): In case you just want to check schema
        """
        name = 'CoordinateTool'
        description = 'Tool for fetching coordinates of a given location using PostGIS'
        version = '0.1'
        self.tool_type = 'AUA'
        super().__init__(name, description, version)

    async def run(self, place_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch coordinates for the given place name.

        Args:
            place_name (str): Name of the place to fetch coordinates for.

        Returns:
            dict: Dictionary containing place name and coordinates, or None if not found.
        """
        
        result = await asyncio.to_thread(get_coords, place_name)
        if result:
            return {
                "place": result[0][0],
                "longitude": result[0][1],
                "latitude": result[0][2]
            }
        return None

def get_coords(place_name: str) -> Optional[list]:
    with st.session_state['db_session']() as session:
        query = text("""
                    WITH ranked_places AS (
                    SELECT
                    name,
                    way,
                        similarity(lower(name), lower(:place_name)) AS sim 
                    FROM
                        planet_osm_point
                    WHERE
                        place IS NOT NULL
                        AND name IS NOT NULL 
                    ORDER BY
                        sim DESC 
                    LIMIT 1 
                )
                SELECT
                    name,
                    ST_X(ST_Transform(ST_Centroid(way), 4326)) AS longitude, 
                    ST_Y(ST_Transform(ST_Centroid(way), 4326)) AS latitude 
                FROM
                    ranked_places;
                    """)
        result = session.execute(query, {"place_name": f"%{place_name}%"})
        rows = result.fetchall()
     
    return rows if rows else None

async def main() -> None:
    """Runs module in test mode"""
    import asyncio
    import time
    model = CoordinateTool()
    place = input('Enter place name: ')
    task_1 = asyncio.create_task(model.run(place))
    print('Started running coordinate tool 1')
    task_2 = asyncio.create_task(model.run(place))
    print('Started running coordinate tool 2')
    remaining = [asyncio.create_task(model.run(place)) for i in range(50)]
    t0 = time.time()
    await asyncio.gather(task_1, task_2, *remaining)
    print(f'Time Taken to run 52 tasks = {time.time() - t0}')
    print(task_1)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
    asyncio.run(main())
    print('Finished')